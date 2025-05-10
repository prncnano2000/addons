from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class Specialite(models.Model):
    _name = "gestion_hospital.specialite"
    _description = "Spécialité médicale"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name asc"

    name = fields.Char(
        string="Nom de la spécialité",
        required=0,
        tracking=True,
        help="Nom complet de la spécialité médicale",
    )
    code = fields.Char(
        string="Code",
        required=0,
        tracking=True,
        help="Code unique identifiant la spécialité",
        copy=False,
    )
    description = fields.Html(
        string="Description",
        help="Description détaillée de la spécialité et de son domaine d'expertise",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
        help="Désactiver pour archiver la spécialité",
    )

    # Relations
    medecin_ids = fields.One2many(
        "gestion_hospital.medecin",
        "specialite_id",
        string="Médecins",
        domain=[("active", "=", True)],
    )
    consultation_ids = fields.One2many(
        "gestion_hospital.consultation",
        "specialite_id",
        string="Consultations",
        domain=[("state", "!=", "annulee")],
    )
    chambre_ids = fields.One2many(
        "gestion_hospital.chambre",
        "specialite_id",
        string="Chambres",
        domain=[("state", "!=", "maintenance")],
    )
    hospitalisation_ids = fields.One2many(
        "gestion_hospital.hospitalisation",
        "specialite_id",
        string="Hospitalisations",
        domain=[("state", "!=", "annulee")],
    )

    # Statistiques
    nombre_lits = fields.Integer(
        string="Nombre total de lits",
        compute="_compute_statistiques",
        store=True,
        help="Nombre total de lits disponibles pour cette spécialité",
    )
    lits_disponibles = fields.Integer(
        string="Lits disponibles", compute="_compute_statistiques", store=True
    )
    lits_occupes = fields.Integer(
        string="Lits occupés", compute="_compute_statistiques", store=True
    )
    taux_occupation = fields.Float(
        string="Taux d'occupation (%)",
        compute="_compute_statistiques",
        store=True,
        digits=(5, 2),
    )
    nombre_medecins = fields.Integer(
        string="Nombre de médecins", compute="_compute_statistiques", store=True
    )
    nombre_consultations = fields.Integer(
        string="Consultations (30j)",
        compute="_compute_statistiques",
        help="Nombre de consultations dans les 30 derniers jours",
    )
    nombre_hospitalisations = fields.Integer(
        string="Hospitalisations actives", compute="_compute_statistiques"
    )

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "Le code de spécialité doit être unique"),
        ("name_unique", "UNIQUE(name)", "Le nom de spécialité doit être unique"),
    ]

    @api.depends(
        "medecin_ids",
        "chambre_ids",
        "chambre_ids.capacite",
        "chambre_ids.lits_occupes",
        "consultation_ids.date_consultation",
        "hospitalisation_ids",
        "hospitalisation_ids.state",
    )
    def _compute_statistiques(self):
        for spec in self:
            # Médecins
            spec.nombre_medecins = len(spec.medecin_ids)

            # Lits
            spec.nombre_lits = sum(chambre.capacite for chambre in spec.chambre_ids)
            spec.lits_occupes = sum(
                chambre.lits_occupes for chambre in spec.chambre_ids
            )
            spec.lits_disponibles = max(0, spec.nombre_lits - spec.lits_occupes)

            # Taux d'occupation
            if spec.nombre_lits > 0:
                spec.taux_occupation = (spec.lits_occupes / spec.nombre_lits) * 100
            else:
                spec.taux_occupation = 0.0

            # Consultations récentes (30 jours)
            date_limite = fields.Datetime.now() - timedelta(days=30)
            spec.nombre_consultations = len(
                spec.consultation_ids.filtered(
                    lambda c: c.date_consultation >= date_limite
                )
            )

            # Hospitalisations actives
            spec.nombre_hospitalisations = len(
                spec.hospitalisation_ids.filtered(lambda h: h.state == "en_cours")
            )

    def action_voir_medecins(self):
        self.ensure_one()
        return {
            "name": _("Médecins de %s") % self.name,
            "type": "ir.actions.act_window",
            "res_model": "gestion_hospital.medecin",
            "view_mode": "tree,kanban,form",
            "domain": [("specialite_id", "=", self.id)],
            "context": {"default_specialite_id": self.id, "search_default_active": 1},
        }

    def action_voir_consultations(self):
        self.ensure_one()
        return {
            "name": _("Consultations de %s") % self.name,
            "type": "ir.actions.act_window",
            "res_model": "gestion_hospital.consultation",
            "view_mode": "tree,calendar,form",
            "domain": [("specialite_id", "=", self.id)],
            "context": {
                "default_specialite_id": self.id,
                "search_default_this_month": 1,
            },
        }

    def action_voir_hospitalisations(self):
        self.ensure_one()
        return {
            "name": _("Hospitalisations de %s") % self.name,
            "type": "ir.actions.act_window",
            "res_model": "gestion_hospital.hospitalisation",
            "view_mode": "tree,form",
            "domain": [("specialite_id", "=", self.id)],
            "context": {"default_specialite_id": self.id, "search_default_en_cours": 1},
        }

    def action_voir_chambres(self):
        self.ensure_one()
        return {
            "name": _("Chambres de %s") % self.name,
            "type": "ir.actions.act_window",
            "res_model": "gestion_hospital.chambre",
            "view_mode": "tree,form",
            "domain": [("specialite_id", "=", self.id)],
            "context": {
                "default_specialite_id": self.id,
                "search_default_disponible": 1,
            },
        }

    @api.model
    def create(self, vals):
        if "code" not in vals:
            vals["code"] = self.env["ir.sequence"].next_by_code(
                "gestion_hospital.specialite"
            ) or _("NEW")
        return super().create(vals)

    @api.constrains("code")
    def _check_code_format(self):
        for specialite in self:
            if specialite.code and not specialite.code.isalnum():
                raise ValidationError(
                    _("Le code doit contenir uniquement des lettres et des chiffres")
                )
