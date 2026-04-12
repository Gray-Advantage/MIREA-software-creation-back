from django.db import models

LEGAL_FORM_CHOICES = [
    ("OOO", "ООО"),
    ("IP", "ИП"),
    ("ZAO", "ЗАО"),
    ("PAO", "ПАО"),
    ("OAO", "ОАО"),
    ("GUP", "ГУП"),
    ("MUP", "МУП"),
    ("PAT", "ПАТ"),
]

ROLE_CHOICES = [
    ("admin", "Администратор"),
    ("employee", "Сотрудник"),
]


class Company(models.Model):
    name = models.CharField("Название", max_length=255)
    logo = models.CharField(
        "Лого (путь)",
        max_length=500,
        blank=True,
        default="",
    )
    legal_form = models.CharField(
        "Орг.-правовая форма",
        max_length=50,
        choices=LEGAL_FORM_CHOICES,
    )
    legal_address = models.TextField("Юридический адрес")
    contact_name = models.CharField("Контактный телефон", max_length=20)
    business_area = models.CharField("Сфера деятельности", max_length=255)
    email = models.EmailField("Почта", unique=True)
    inn = models.CharField("ИНН", max_length=12, blank=True, default="")
    bik = models.CharField("БИК", max_length=9, blank=True, default="")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        managed = False
        db_table = "company"
        verbose_name = "Компания"
        verbose_name_plural = "Компании"

    def __str__(self) -> str:
        return self.name


class AppUser(models.Model):
    email = models.EmailField("Email", unique=True)
    password_hash = models.CharField("Хеш пароля", max_length=255)
    role = models.CharField("Роль", max_length=20, choices=ROLE_CHOICES)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name="Компания",
        db_column="company_id",
    )
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        managed = False
        db_table = "user"
        verbose_name = "Пользователь приложения"
        verbose_name_plural = "Пользователи приложения"

    def __str__(self) -> str:
        return f"{self.email} ({self.get_role_display()})"
