from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Chambre(models.Model):
    _name = "gestion_hospital.chambre"
    _description = "Chambre d'hôpital"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "numero"

    name = fields.Char(string="Nom", compute="_compute_name", store=True)
    numero = fields.Char(string="Numéro", required=0, tracking=True)
    specialite_id = fields.Many2one(
        "gestion_hospital.specialite", string="Spécialité", required=0, tracking=True
    )
    capacite = fields.Integer(
        string="Capacité (lits)",
        default=1,
        tracking=True,
        help="Nombre maximum de lits dans la chambre",
    )
    type = fields.Selection(
        [
            ("simple", "Simple"),
            ("double", "Double"),
            ("triple", "Triple"),
            ("suite", "Suite"),
            ("autre", "Autre"),
        ],
        string="Type de chambre",
        default="simple",
        tracking=True,
    )
    equipements = fields.Text(
        string="Équipements", help="Liste des équipements disponibles dans la chambre"
    )
    notes = fields.Text(string="Notes")
    state = fields.Selection(
        [
            ("disponible", "Disponible"),
            ("partiellement", "Partiellement occupée"),
            ("occupee", "Occupée"),
            ("maintenance", "En maintenance"),
            ("reservee", "Réservée"),
        ],
        string="État",
        default="disponible",
        tracking=True,
    )

    # Relations
    hospitalisation_ids = fields.One2many(
        "gestion_hospital.hospitalisation", "chambre_id", string="Hospitalisations"
    )

    # Champs calculés
    lits_occupes = fields.Integer(
        string="Lits occupés", compute="_compute_lits_occupes", store=True
    )
    taux_occupation = fields.Float(
        string="Taux d'occupation (%)",
        compute="_compute_taux_occupation",
        store=True,
        digits=(5, 2),  # 2 décimales
    )
    
    company_id = fields.Many2one(
        'res.company', 
        string='Société', 
        default=lambda self: self.env.company,
        tracking=True
    )

    _sql_constraints = [
        ("numero_unique", "UNIQUE(numero, company_id)", "Le numéro de chambre doit être unique dans cette société"),
        ("capacite_positive", "CHECK(capacite > 0)", "La capacité doit être positive"),
    ]

    @api.depends("numero", "specialite_id")
    def _compute_name(self):
        for chambre in self:
            chambre.name = f"{chambre.specialite_id.name or 'Chambre'} {chambre.numero or ''}".strip()

    @api.depends("hospitalisation_ids", "hospitalisation_ids.state")
    def _compute_lits_occupes(self):
        for chambre in self:
            hospitalisations_en_cours = chambre.hospitalisation_ids.filtered(
                lambda h: h.state == "en_cours"
            )
            chambre.lits_occupes = len(hospitalisations_en_cours)

    @api.depends("capacite", "lits_occupes")
    def _compute_taux_occupation(self):
        for chambre in self:
            chambre.taux_occupation = 0
            if chambre.capacite > 0:
                chambre.taux_occupation = (
                    chambre.lits_occupes / chambre.capacite
                ) * 100

    @api.onchange("lits_occupes", "capacite")
    def _onchange_occupation(self):
        for chambre in self:
            if chambre.lits_occupes >= chambre.capacite:
                chambre.state = "occupee"
            elif chambre.lits_occupes > 0 and chambre.state == "disponible":
                chambre.state = "partiellement"
            elif chambre.lits_occupes == 0 and chambre.state != "maintenance":
                chambre.state = "disponible"

    def action_voir_hospitalisations(self):
        self.ensure_one()
        return {
            "name": _("Hospitalisations"),
            "type": "ir.actions.act_window",
            "res_model": "gestion_hospital.hospitalisation",
            "view_mode": "tree,form",
            "domain": [("chambre_id", "=", self.id)],
            "context": {"default_chambre_id": self.id},
        }

    @api.model
    def create(self, vals):
        # Validation supplémentaire si nécessaire
        if "capacite" in vals and vals.get("capacite") <= 0:
            raise UserError(_("La capacité doit être positive"))
        return super(Chambre, self).create(vals)
