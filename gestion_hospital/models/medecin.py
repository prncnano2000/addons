from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Medecin(models.Model):
    _name = "gestion_hospital.medecin"
    _description = "Médecin"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(
        string="Nom complet",
        required=True,
        tracking=True,
        help="Nom et prénom du médecin",
    )
    matricule = fields.Char(
        string="Matricule",
        required=True,
        tracking=True,
        copy=False,
        help="Identifiant unique du médecin",
    )
    specialite_id = fields.Many2one(
        "gestion_hospital.specialite",
        string="Spécialité",
        required=False,
        tracking=True,
        help="Spécialité médicale principale",
    )
    telephone = fields.Char(
        string="Téléphone", tracking=True, help="Numéro de téléphone professionnel"
    )
    email = fields.Char(
        string="Email", tracking=True, help="Adresse email professionnelle"
    )
    consultation_ids = fields.One2many(
        "gestion_hospital.consultation",
        "medecin_id",
        string="Consultations",
        domain=[("state", "!=", "annulee")],
    )
    hospitalisation_ids = fields.One2many(
        "gestion_hospital.hospitalisation",
        "medecin_id",
        string="Hospitalisations",
        domain=[("state", "!=", "annulee")],
    )
    disponibilite = fields.Boolean(
        string="Disponible",
        default=True,
        tracking=True,
        compute="_compute_disponibilite",
        store=True,
        help="Indique si le médecin est actuellement disponible",
    )
    horaires_travail = fields.Text(
        string="Horaires de travail", help="Jours et heures de travail habituels"
    )
    competences = fields.Text(
        string="Compétences", help="Compétences et certifications particulières"
    )
    state = fields.Selection(
        [
            ("actif", "Actif"),
            ("inactif", "Inactif"),
            ("conge", "En congé"),
            ("formation", "En formation"),
        ],
        string="État",
        default="actif",
        tracking=True,
        group_expand="_expand_states",
    )
    active = fields.Boolean(
        string="Actif",
        default=True,
        tracking=True,
        help="Désactivez pour archiver le médecin",
    )

    # Champs calculés
    nombre_consultations = fields.Integer(
        string="Nombre de consultations", compute="_compute_stats", store=True
    )
    nombre_hospitalisations = fields.Integer(
        string="Nombre d'hospitalisations", compute="_compute_stats", store=True
    )
    consultations_aujourdhui = fields.Integer(
        string="Consultations aujourd'hui", compute="_compute_consultations_aujourdhui"
    )
    taux_occupation = fields.Float(
        string="Taux d'occupation (%)",
        compute="_compute_taux_occupation",
        digits=(5, 2),
    )

    _sql_constraints = [
        ("matricule_unique", "UNIQUE(matricule)", "Le matricule doit être unique"),
        ("email_unique", "UNIQUE(email)", "L'email doit être unique"),
    ]

    @api.depends("consultation_ids", "hospitalisation_ids")
    def _compute_stats(self):
        for medecin in self:
            medecin.nombre_consultations = len(medecin.consultation_ids)
            medecin.nombre_hospitalisations = len(medecin.hospitalisation_ids)

    @api.depends("consultation_ids.date_consultation")
    def _compute_consultations_aujourdhui(self):
        today = fields.Date.today()
        for medecin in self:
            medecin.consultations_aujourdhui = len(
                medecin.consultation_ids.filtered(
                    lambda c: c.date_consultation.date() == today
                    and c.state != "annulee"
                )
            )

    @api.depends("state")
    def _compute_disponibilite(self):
        for medecin in self:
            medecin.disponibilite = medecin.state == "actif"

    def _compute_taux_occupation(self):
        for medecin in self:
            total_creneaux = 40  # Par exemple, 40 créneaux par semaine
            creneaux_occupes = medecin.nombre_consultations / 2  # Exemple de calcul
            if total_creneaux > 0:
                medecin.taux_occupation = (creneaux_occupes / total_creneaux) * 100
            else:
                medecin.taux_occupation = 0

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    def action_voir_consultations(self):
        self.ensure_one()
        return {
            "name": _("Consultations du médecin"),
            "type": "ir.actions.act_window",
            "res_model": "gestion_hospital.consultation",
            "view_mode": "tree,calendar,form",
            "domain": [("medecin_id", "=", self.id), ("state", "!=", "annulee")],
            "context": {"default_medecin_id": self.id, "search_default_this_week": 1},
        }

    def action_voir_hospitalisations(self):
        self.ensure_one()
        return {
            "name": _("Hospitalisations du médecin"),
            "type": "ir.actions.act_window",
            "res_model": "gestion_hospital.hospitalisation",
            "view_mode": "tree,form",
            "domain": [("medecin_id", "=", self.id), ("state", "!=", "annulee")],
            "context": {"default_medecin_id": self.id, "search_default_en_cours": 1},
        }

    def action_marquer_actif(self):
        self.write({"state": "actif"})

    def action_marquer_inactif(self):
        self.write({"state": "inactif"})

    def action_marquer_conge(self):
        self.write({"state": "conge"})
    
    def action_marquer_formation(self):
        self.write({"state": "formation"})

    @api.constrains("email")
    def _check_email(self):
        for medecin in self:
            if medecin.email and "@" not in medecin.email:
                raise ValidationError(_("L'adresse email doit être valide"))

    @api.model
    def create(self, vals):
        if "matricule" not in vals:
            vals["matricule"] = self.env["ir.sequence"].next_by_code(
                "gestion_hospital.medecin"
            ) or _("Nouveau")
        return super().create(vals)
