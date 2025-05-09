from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Consultation(models.Model):
    _name = "gestion_hospital.consultation"
    _description = "Consultation médicale"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_consultation desc"

    name = fields.Char(
        string="Référence",
        readonly=True,
        default=lambda self: _("Nouvelle"),
        copy=False,
    )
    patient_id = fields.Many2one(
        "gestion_hospital.patient", string="Patient", required=True, tracking=True
    )
    medecin_id = fields.Many2one(
        "gestion_hospital.medecin", string="Médecin", required=True, tracking=True
    )
    specialite_id = fields.Many2one(
        "gestion_hospital.specialite", string="Spécialité", required=True, tracking=True
    )
    date_consultation = fields.Datetime(
        string="Date de consultation",
        default=fields.Datetime.now,
        tracking=True,
        help="Date et heure prévues pour la consultation",
    )
    date_fin = fields.Datetime(string="Date de fin", readonly=True, tracking=True)
    duree = fields.Float(
        string="Durée (heures)", compute="_compute_duree", store=True, digits=(2, 2)
    )
    motif = fields.Text(string="Motif de consultation", required=True, tracking=True)
    diagnostic = fields.Text(string="Diagnostic", tracking=True)
    prescription = fields.Text(string="Prescription", tracking=True)
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
    document_ids = fields.Many2many("ir.attachment", string="Documents joints")
    
    company_id = fields.Many2one(
        'res.company', 
        string='Société', 
        default=lambda self: self.env.company,
        tracking=True
    )

    _sql_constraints = [
        ("montant_positif", "CHECK(montant >= 0)", "Le montant doit être positif"),
        (
            "date_coherence",
            "CHECK(date_fin >= date_consultation OR date_fin IS NULL)",
            "La date de fin doit être postérieure à la date de début",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("Nouvelle")) == _("Nouvelle"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "gestion_hospital.consultation"
                ) or _("Nouvelle")
        return super().create(vals_list)

    @api.depends("date_consultation", "date_fin")
    def _compute_duree(self):
        for consultation in self:
            if consultation.date_consultation and consultation.date_fin:
                delta = consultation.date_fin - consultation.date_consultation
                consultation.duree = delta.total_seconds() / 3600  # Convertir en heures
            else:
                consultation.duree = 0.0

    @api.onchange("medecin_id")
    def _onchange_medecin_id(self):
        if self.medecin_id:
            self.specialite_id = self.medecin_id.specialite_id
            
    @api.onchange("patient_id")
    def _onchange_patient_id(self):
        if self.patient_id and self.patient_id.medecin_traitant_id:
            self.medecin_id = self.patient_id.medecin_traitant_id

    def action_planifier(self):
        self.write({"state": "planifiee"})

    def action_demarrer(self):
        for consultation in self:
            if consultation.state == "planifiee":
                consultation.write(
                    {"state": "en_cours", "date_consultation": fields.Datetime.now()}
                )

    def action_terminer(self):
        for consultation in self:
            if consultation.state == "en_cours":
                consultation.write(
                    {"state": "terminee", "date_fin": fields.Datetime.now()}
                )

    def action_annuler(self):
        for consultation in self:
            if consultation.state in ["planifiee", "en_cours"]:
                consultation.write(
                    {
                        "state": "annulee",
                        "date_fin": (
                            fields.Datetime.now()
                            if consultation.state == "en_cours"
                            else False
                        ),
                    }
                )
                
    def action_marquer_paye(self):
        self.write({"paiement": "paye"})
        
    def action_marquer_partiel(self):
        self.write({"paiement": "partiel"})

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.constrains("date_consultation")
    def _check_date_consultation(self):
        for consultation in self:
            if consultation.date_consultation.date() < fields.Date.today():
                raise ValidationError(
                    _("La date de consultation ne peut pas être dans le passé")
                )

    @api.constrains("montant", "paiement")
    def _check_paiement(self):
        for consultation in self:
            if consultation.paiement == "paye" and consultation.montant <= 0:
                raise ValidationError(
                    _("Une consultation payée doit avoir un montant positif")
                )
