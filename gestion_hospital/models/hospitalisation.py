from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class Hospitalisation(models.Model):
    _name = "gestion_hospital.hospitalisation"
    _description = "Hospitalisation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_admission desc"

    name = fields.Char(
        string="Référence",
        readonly=True,
        default=lambda self: _("Nouvelle"),
        copy=False,
    )
    patient_id = fields.Many2one(
        "gestion_hospital.patient",
        string="Patient",
        required=True,
        tracking=True,
        domain=[("active", "=", True)],
    )
    medecin_id = fields.Many2one(
        "gestion_hospital.medecin",
        string="Médecin traitant",
        required=True,
        tracking=True,
        domain=[("active", "=", True)],
    )
    specialite_id = fields.Many2one(
        "gestion_hospital.specialite", string="Spécialité", required=True, tracking=True
    )
    chambre_id = fields.Many2one(
        "gestion_hospital.chambre",
        string="Chambre",
        required=True,
        tracking=True,
        domain="[('specialite_id', '=?', specialite_id), ('state', '!=', 'occupee')]",
    )

    date_admission = fields.Datetime(
        string="Date d'admission",
        default=fields.Datetime.now,
        tracking=True,
        help="Date et heure d'admission effective du patient",
    )
    date_sortie = fields.Datetime(
        string="Date de sortie prévue",
        compute="_compute_date_sortie",
        store=True,
        tracking=True,
    )
    date_sortie_reelle = fields.Datetime(
        string="Date de sortie réelle",
        tracking=True,
        help="Date et heure de sortie effective du patient",
    )

    motif = fields.Text(string="Motif d'hospitalisation", required=True, tracking=True)
    diagnostic = fields.Text(string="Diagnostic", tracking=True)
    traitement = fields.Text(string="Traitement", tracking=True)
    notes = fields.Text(string="Notes")

    state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("planifiee", "Planifiée"),
            ("en_cours", "En cours"),
            ("terminee", "Terminée"),
            ("annulee", "Annulée"),
        ],
        string="État",
        default="draft",
        tracking=True,
        group_expand="_expand_states",
    )

    montant = fields.Float(string="Montant", tracking=True, digits="Account")
    paiement = fields.Selection(
        [("non_paye", "Non payé"), ("partiel", "Partiellement payé"), ("paye", "Payé")],
        string="État du paiement",
        default="non_paye",
        tracking=True,
    )

    # Champs calculés
    duree_jours = fields.Integer(
        string="Durée (jours)", compute="_compute_duree", store=True
    )
    duree_heures = fields.Float(
        string="Durée (heures)", compute="_compute_duree", store=True, digits=(12, 2)
    )
    duree_str = fields.Char(string="Durée", compute="_compute_duree_str")
    
    company_id = fields.Many2one(
        'res.company', 
        string='Société', 
        default=lambda self: self.env.company,
        tracking=True
    )

    _sql_constraints = [
        (
            "montant_positif",
            "CHECK(montant >= 0)",
            "Le montant doit être positif ou nul",
        ),
        (
            "date_coherence",
            "CHECK(date_sortie_reelle >= date_admission OR date_sortie_reelle IS NULL)",
            "La date de sortie doit être postérieure à la date d'admission",
        ),
        (
            "chambre_unique",
            "unique(chambre_id, patient_id, state, company_id)",
            "Un patient ne peut avoir qu'une hospitalisation active par chambre",
        ),
    ]

    @api.depends("date_admission", "date_sortie_reelle", "state")
    def _compute_duree(self):
        now = fields.Datetime.now()
        for hosp in self:
            start_date = hosp.date_admission
            end_date = hosp.date_sortie_reelle if hosp.state == "terminee" else now

            if start_date and end_date:
                delta = end_date - start_date
                hosp.duree_jours = delta.days
                hosp.duree_heures = delta.total_seconds() / 3600
            else:
                hosp.duree_jours = 0
                hosp.duree_heures = 0.0

    def _compute_duree_str(self):
        for hosp in self:
            if hosp.duree_jours > 0:
                hosp.duree_str = f"{hosp.duree_jours} jours"
            elif hosp.duree_heures > 0:
                hosp.duree_str = f"{hosp.duree_heures:.2f} heures"
            else:
                hosp.duree_str = "0 heure"

    @api.depends("date_admission")
    def _compute_date_sortie(self):
        for hosp in self:
            if hosp.date_admission:
                hosp.date_sortie = hosp.date_admission + timedelta(days=7)
            else:
                hosp.date_sortie = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("Nouvelle")) == _("Nouvelle"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "gestion_hospital.hospitalisation"
                ) or _("Nouvelle")
        return super().create(vals_list)

    @api.onchange("medecin_id")
    def _onchange_medecin_id(self):
        if self.medecin_id:
            self.specialite_id = self.medecin_id.specialite_id

    @api.onchange("patient_id")
    def _onchange_patient_id(self):
        if self.patient_id and self.patient_id.medecin_traitant_id:
            self.medecin_id = self.patient_id.medecin_traitant_id

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    def action_planifier(self):
        self.write({"state": "planifiee"})

    def action_admettre(self):
        for hosp in self:
            if hosp.state != "planifiee":
                raise UserError(
                    _("Seules les hospitalisations planifiées peuvent être admises")
                )

            if not hosp.chambre_id or hosp.chambre_id.state == "occupee":
                raise UserError(_("Veuillez sélectionner une chambre disponible"))

            hosp.write({"state": "en_cours", "date_admission": fields.Datetime.now()})
            hosp.chambre_id.write(
                {
                    "lits_occupes": hosp.chambre_id.lits_occupes + 1,
                    "state": (
                        "occupee"
                        if hosp.chambre_id.lits_occupes + 1 >= hosp.chambre_id.capacite
                        else "partiellement"
                    ),
                }
            )

    def action_terminer(self):
        now = fields.Datetime.now()
        for hosp in self:
            if hosp.state != "en_cours":
                raise UserError(
                    _("Seules les hospitalisations en cours peuvent être terminées")
                )

            hosp.write({"state": "terminee", "date_sortie_reelle": now})
            hosp.chambre_id.write(
                {
                    "lits_occupes": hosp.chambre_id.lits_occupes - 1,
                    "state": (
                        "disponible"
                        if hosp.chambre_id.lits_occupes - 1 <= 0
                        else "partiellement"
                    ),
                }
            )

    def action_annuler(self):
        for hosp in self:
            if hosp.state == "terminee":
                raise UserError(
                    _("Une hospitalisation terminée ne peut pas être annulée")
                )

            if hosp.state == "en_cours":
                hosp.chambre_id.write(
                    {
                        "lits_occupes": hosp.chambre_id.lits_occupes - 1,
                        "state": (
                            "disponible"
                            if hosp.chambre_id.lits_occupes - 1 <= 0
                            else "partiellement"
                        ),
                    }
                )
            hosp.write({"state": "annulee"})

    def action_marquer_paye(self):
        self._check_paiement_possible()
        self.write({"paiement": "paye"})

    def action_marquer_partiel(self):
        self._check_paiement_possible()
        self.write({"paiement": "partiel"})

    def _check_paiement_possible(self):
        for hosp in self:
            if hosp.state == "annulee":
                raise UserError(_("Une hospitalisation annulée ne peut pas être payée"))
            if hosp.montant <= 0:
                raise UserError(
                    _("Le montant doit être positif pour enregistrer un paiement")
                )

    def action_voir_patient(self):
        self.ensure_one()
        return {
            'name': _('Patient'),
            'type': 'ir.actions.act_window',
            'res_model': 'gestion_hospital.patient',
            'view_mode': 'form',
            'res_id': self.patient_id.id,
        }
        
    @api.constrains("chambre_id", "state")
    def _check_chambre_disponibilite(self):
        for hosp in self:
            if hosp.state in ["planifiee", "en_cours"] and hosp.chambre_id:
                if hosp.chambre_id.state == "occupee":
                    raise ValidationError(
                        _("La chambre sélectionnée est déjà occupée")
                    )
                if hosp.chambre_id.lits_occupes >= hosp.chambre_id.capacite:
                    raise ValidationError(
                        _("La chambre sélectionnée est déjà pleine")
                    )

    @api.constrains("date_admission")
    def _check_date_admission(self):
        for hosp in self:
            if hosp.date_admission and hosp.date_admission > fields.Datetime.now():
                raise ValidationError(
                    _("La date d'admission ne peut pas être dans le futur")
                )
