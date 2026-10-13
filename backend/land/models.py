from django.db import models


class District(models.Model):
    name_en = models.CharField(max_length=80, unique=True)
    name_bn = models.CharField(max_length=80)

    class Meta:
        ordering = ["name_en"]

    def __str__(self):
        return self.name_en


class Upazila(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="upazilas")
    name_en = models.CharField(max_length=80)
    name_bn = models.CharField(max_length=80)

    class Meta:
        ordering = ["name_en"]
        unique_together = [("district", "name_en")]

    def __str__(self):
        return f"{self.name_en}, {self.district}"


class Mouza(models.Model):
    upazila = models.ForeignKey(Upazila, on_delete=models.CASCADE, related_name="mouzas")
    name_en = models.CharField(max_length=80)
    name_bn = models.CharField(max_length=80)
    jl_no = models.PositiveIntegerField(help_text="Jurisdiction list number")

    class Meta:
        ordering = ["name_en"]
        unique_together = [("upazila", "name_en")]

    def __str__(self):
        return f"{self.name_en} (JL {self.jl_no})"


class Person(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    class Religion(models.TextChoices):
        MUSLIM = "muslim", "Muslim"
        HINDU = "hindu", "Hindu"
        OTHER = "other", "Other"

    name_en = models.CharField(max_length=120)
    name_bn = models.CharField(max_length=120)
    father_name_en = models.CharField(max_length=120, blank=True)
    father_name_bn = models.CharField(max_length=120, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, default=Gender.MALE)
    religion = models.CharField(max_length=10, choices=Religion.choices, default=Religion.MUSLIM)
    is_minor = models.BooleanField(default=False)
    is_deceased = models.BooleanField(default=False)
    date_of_death = models.DateField(null=True, blank=True)
    is_government = models.BooleanField(default=False, help_text="Government / khas khatian holder")
    nid = models.CharField(max_length=20, blank=True, help_text="Synthetic NID only")

    class Meta:
        ordering = ["name_en"]
        verbose_name_plural = "people"

    def __str__(self):
        return self.name_en


class HeirLink(models.Model):
    class Relation(models.TextChoices):
        HUSBAND = "husband", "Husband"
        WIFE = "wife", "Wife"
        SON = "son", "Son"
        DAUGHTER = "daughter", "Daughter"
        FATHER = "father", "Father"
        MOTHER = "mother", "Mother"

    deceased = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="heir_links")
    heir = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="inherited_from")
    relation = models.CharField(max_length=10, choices=Relation.choices)

    class Meta:
        unique_together = [("deceased", "heir")]

    def __str__(self):
        return f"{self.heir} ({self.relation} of {self.deceased})"


class Plot(models.Model):
    class LandClass(models.TextChoices):
        AGRICULTURAL = "agricultural", "Agricultural (Nal)"
        HOMESTEAD = "homestead", "Homestead (Bhiti)"
        COMMERCIAL = "commercial", "Commercial"
        POND = "pond", "Pond (Doba)"

    mouza = models.ForeignKey(Mouza, on_delete=models.CASCADE, related_name="plots")
    dag_no = models.CharField(max_length=20)
    area_acre = models.DecimalField(max_digits=8, decimal_places=4)
    land_class = models.CharField(max_length=20, choices=LandClass.choices, default=LandClass.AGRICULTURAL)
    mouza_rate_per_acre = models.PositiveIntegerField(help_text="Government minimum value per acre (BDT)")

    class Meta:
        ordering = ["mouza", "dag_no"]
        unique_together = [("mouza", "dag_no")]

    def __str__(self):
        return f"Dag {self.dag_no}, {self.mouza.name_en}"


class Khatian(models.Model):
    class Survey(models.TextChoices):
        CS = "CS", "CS (Cadastral Survey)"
        SA = "SA", "SA (State Acquisition)"
        RS = "RS", "RS (Revisional Survey)"
        BS = "BS", "BS (Bangladesh Survey)"
        NAMJARI = "NAMJARI", "Mutation khatian"

    SURVEY_ORDER = {"CS": 1, "SA": 2, "RS": 3, "BS": 4, "NAMJARI": 5}

    mouza = models.ForeignKey(Mouza, on_delete=models.CASCADE, related_name="khatians")
    khatian_no = models.CharField(max_length=20)
    survey = models.CharField(max_length=10, choices=Survey.choices)
    record_year = models.PositiveIntegerField()
    plots = models.ManyToManyField(Plot, related_name="khatians")

    class Meta:
        ordering = ["mouza", "record_year", "khatian_no"]
        unique_together = [("mouza", "survey", "khatian_no")]

    @property
    def order(self):
        return (self.SURVEY_ORDER[self.survey], self.record_year, self.pk or 0)

    def __str__(self):
        return f"{self.survey} khatian {self.khatian_no} ({self.mouza.name_en})"


class KhatianOwner(models.Model):
    khatian = models.ForeignKey(Khatian, on_delete=models.CASCADE, related_name="owners")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="khatian_shares")
    share = models.DecimalField(max_digits=7, decimal_places=6, help_text="Fraction of each plot, e.g. 0.5")

    class Meta:
        unique_together = [("khatian", "person")]

    def __str__(self):
        return f"{self.person} — {self.share} of {self.khatian}"


class Deed(models.Model):
    class DeedType(models.TextChoices):
        SALE = "sale", "Sale (Saf-kobla)"
        HEBA = "heba", "Gift (Heba)"
        EXCHANGE = "exchange", "Exchange"
        PARTITION = "partition", "Partition (Bontonnama)"

    class Status(models.TextChoices):
        REGISTERED = "registered", "Registered"
        CANCELLED = "cancelled", "Cancelled by court"

    deed_no = models.CharField(max_length=30, unique=True)
    deed_type = models.CharField(max_length=20, choices=DeedType.choices, default=DeedType.SALE)
    registration_date = models.DateField()
    sub_registry_office = models.CharField(max_length=80)
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="deeds")
    area_acre = models.DecimalField(max_digits=8, decimal_places=4)
    price_bdt = models.PositiveBigIntegerField(default=0)
    sellers = models.ManyToManyField(Person, related_name="deeds_as_seller")
    buyers = models.ManyToManyField(Person, related_name="deeds_as_buyer")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REGISTERED)

    class Meta:
        ordering = ["registration_date"]

    def __str__(self):
        return f"Deed {self.deed_no} ({self.registration_date})"


class Bainanama(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    agreement_no = models.CharField(max_length=30, unique=True)
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="bainanamas")
    seller = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="bainanamas_as_seller")
    buyer = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="bainanamas_as_buyer")
    area_acre = models.DecimalField(max_digits=8, decimal_places=4)
    agreement_date = models.DateField()
    is_registered = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        verbose_name = "bainanama (agreement for sale)"

    def __str__(self):
        return f"Bainanama {self.agreement_no}"


class Mutation(models.Model):
    class Status(models.TextChoices):
        APPROVED = "approved", "Approved"
        PENDING = "pending", "Pending"
        REJECTED = "rejected", "Rejected"

    case_no = models.CharField(max_length=30, unique=True)
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="mutations")
    new_owner = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="mutations")
    deed = models.ForeignKey(Deed, on_delete=models.SET_NULL, null=True, blank=True, related_name="mutations")
    resulting_khatian = models.ForeignKey(Khatian, on_delete=models.SET_NULL, null=True, blank=True)
    application_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices)

    def __str__(self):
        return f"Mutation {self.case_no} ({self.status})"


class PowerOfAttorney(models.Model):
    class Scope(models.TextChoices):
        SALE = "sale", "Sale and registration"
        MANAGEMENT = "management", "Management only"

    poa_no = models.CharField(max_length=30, unique=True)
    principal = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="poas_given")
    attorney = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="poas_held")
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="poas")
    scope = models.CharField(max_length=20, choices=Scope.choices)
    is_registered = models.BooleanField(default=True)
    is_revoked = models.BooleanField(default=False)
    executed_on = models.DateField()

    class Meta:
        verbose_name = "power of attorney"
        verbose_name_plural = "powers of attorney"

    def __str__(self):
        return f"POA {self.poa_no}"


class LegalStatus(models.Model):
    class StatusType(models.TextChoices):
        CIVIL_SUIT = "civil_suit", "Civil suit"
        TRIBUNAL = "tribunal", "Land Survey Tribunal case"
        INJUNCTION = "injunction", "Injunction on transfer"
        SECTION_144 = "section_144", "Section 144 proceeding"
        ACQUISITION = "acquisition", "Government acquisition"
        KHAS = "khas", "Khas land"
        VESTED = "vested", "Vested property (Orpito)"
        ABANDONED = "abandoned", "Abandoned property"
        WAQF = "waqf", "Waqf estate"
        DEBOTTOR = "debottor", "Debottor property"
        FOREST = "forest", "Reserved forest"

    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="legal_statuses")
    status_type = models.CharField(max_length=20, choices=StatusType.choices)
    reference_no = models.CharField(max_length=60)
    description = models.CharField(max_length=255, blank=True)
    since = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "legal statuses"

    def __str__(self):
        return f"{self.get_status_type_display()} — {self.reference_no}"


class Mortgage(models.Model):
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="mortgages")
    mortgagor = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="mortgages")
    lender = models.CharField(max_length=120)
    amount_bdt = models.PositiveBigIntegerField()
    registered_on = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Mortgage to {self.lender} ({self.plot})"


class TaxRecord(models.Model):
    plot = models.OneToOneField(Plot, on_delete=models.CASCADE, related_name="tax_record")
    holding_no = models.CharField(max_length=30)
    paid_upto_year = models.PositiveIntegerField()
    arrears_bdt = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Holding {self.holding_no}"


class PurchaseIntent(models.Model):
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="purchase_intents")
    buyer_token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Intent on {self.plot} at {self.created_at:%Y-%m-%d}"
