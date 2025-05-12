from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime


class Patient(models.Model):
    _name = "gestion_hospital.patient"
    _description = "Patient"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name asc"

    name = fields.Char(
        string="Nom complet",
        required=True,
        track_visibility="onchange",
        help="Nom et prénom du patient",
    )
    reference = fields.Char(
        string="Référence",
        readonly=True,
        default=lambda self: _("Nouveau"),
        copy=False,
        index=True,
    )
    age = fields.Integer(
        string="Âge",
        compute="_compute_age",
        store=True,
        tracking=True,
        help="Âge calculé à partir de la date de naissance",
    )
    sexe = fields.Selection(
        [
            ("homme", "Homme"),
            ("femme", "Femme"),
            ("non_precise", "Non précisé"),
        ],
        string="Sexe",
        default="non_precise",
        tracking=True,
    )
    date_naissance = fields.Date(
        string="Date de naissance", tracking=True, help="Date de naissance du patient"
    )
    adresse = fields.Text(string="Adresse complète", tracking=True)
    telephone = fields.Char(
        string="Téléphone", tracking=True, help="Numéro de téléphone principal"
    )
    email = fields.Char(string="Email", tracking=True, help="Adresse email de contact")
    groupe_sanguin = fields.Selection(
        [
            ("a+", "A+"),
            ("a-", "A-"),
            ("b+", "B+"),
            ("b-", "B-"),
            ("ab+", "AB+"),
            ("ab-", "AB-"),
            ("o+", "O+"),
            ("o-", "O-"),
            ("inconnu", "Inconnu"),
        ],
        string="Groupe sanguin",
        default="inconnu",
        tracking=True,
    )
    historique_medical = fields.Html(
        string="Historique médical", help="Antécédents médicaux et traitements en cours"
    )
    allergies = fields.Text(
        string="Allergies connues",
        tracking=True,
        help="Liste des allergies médicamenteuses ou alimentaires",
    )
    medecin_traitant_id = fields.Many2one(
        'gestion_hospital.medecin',
        string='Médecin traitant',
        tracking=True
    )
    consultations_ids = fields.One2many(
        'gestion_hospital.consultation',
        'patient_id',
        string='Consultations',
        domain=[('state', '!=', 'annulee')]
    )
    hospitalisation_ids = fields.One2many(
        'gestion_hospital.hospitalisation',
        'patient_id',
        string='Hospitalisations',
        domain=[('state', '!=', 'annulee')]
    )
    state = fields.Selection([
        ('nouveau', 'Nouveau'),
        ('en_cours', 'En traitement'),
        ('gueri', 'Guéri'),
        ('chronique', 'Maladie chronique'),
        ('decede', 'Décédé')
    ],
    string='État',
    default='nouveau',
    tracking=True,
    group_expand='_expand_states'
    )
    active = fields.Boolean(
        string="Actif", default=True, help="Désactiver pour archiver le patient"
    )
    image = fields.Binary(string="Photo", attachment=True)

    _sql_constraints = [
        (
            "telephone_unique",
            "UNIQUE(telephone)",
            "Ce numéro de téléphone est déjà utilisé",
        ),
        ("email_unique", "UNIQUE(email)", "Cet email est déjà utilisé"),
        (
            "date_naissance_valid",
            "CHECK(date_naissance <= current_date)",
            "La date de naissance doit être dans le passé",
        ),
    ]

    @api.depends("date_naissance")
    def _compute_age(self):
        today = date.today()
        for patient in self:
            if patient.date_naissance:
                dob = patient.date_naissance
                patient.age = (
                    today.year
                    - dob.year
                    - ((today.month, today.day) < (dob.month, dob.day))
                )
            else:
                patient.age = 0

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('Nouveau')) == _('Nouveau'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('gestion_hospital.patient') or _('Nouveau')
        return super().create(vals_list)

    def action_voir_consultations(self):
        self.ensure_one()
        return {
            'name': _('Consultations du patient'),
            'type': 'ir.actions.act_window',
            'res_model': 'gestion_hospital.consultation',
            'view_mode': 'tree,form,calendar',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_voir_hospitalisations(self):
        self.ensure_one()
        return {
            'name': _('Hospitalisations du patient'),
            'type': 'ir.actions.act_window',
            'res_model': 'gestion_hospital.hospitalisation',
            'view_mode': 'tree,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_marquer_gueri(self):
        self.write({'state': 'gueri'})

    def action_marquer_en_cours(self):
        self.write({'state': 'en_cours'})

    def action_marquer_decede(self):
        self.write({'state': 'decede'})

    def action_marquer_chronique(self):
        self.write({'state': 'chronique'})

    @api.constrains("email")
    def _check_email(self):
        for patient in self:
            if patient.email and "@" not in patient.email:
                raise ValidationError(_("L'adresse email doit être valide"))

    @api.onchange('medecin_traitant_id')
    def _onchange_medecin_traitant(self):
        if self.medecin_traitant_id:
            return {
                'warning': {
                    'title': _("Médecin traitant assigné"),
                    'message': _("N'oubliez pas d'informer le patient du changement de médecin traitant.")
                }
            }
