from django.db import models

from users.models import AppUser, Company


RATE_TYPE_CHOICES = [
    ("hourly", "Почасовая"),
    ("shift", "За смену"),
    ("daily", "Дневная"),
]

CURRENCY_CHOICES = [
    ("RUB", "Рубли"),
    ("EUR", "Евро"),
    ("USD", "Доллары"),
]

ADJUSTMENT_TYPE_CHOICES = [
    ("bonus", "Премия"),
    ("fine", "Штраф"),
]


class EmployeeProfile(models.Model):
    user = models.OneToOneField(
        AppUser, on_delete=models.CASCADE, verbose_name="Пользователь",
        db_column="user_id",
    )
    first_name = models.CharField("Имя", max_length=100)
    last_name = models.CharField("Фамилия", max_length=100)
    patronymic = models.CharField("Отчество", max_length=100, blank=True, null=True)
    phone = models.CharField("Телефон", max_length=30, blank=True, null=True)
    position = models.CharField("Должность", max_length=255)
    rate_type = models.CharField("Тип ставки", max_length=20, choices=RATE_TYPE_CHOICES)
    rate_amount = models.DecimalField("Сумма ставки", max_digits=10, decimal_places=2)
    currency = models.CharField("Валюта", max_length=3, choices=CURRENCY_CHOICES)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "employee_profile"
        verbose_name = "Профиль сотрудника"
        verbose_name_plural = "Профили сотрудников"

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Adjustment(models.Model):
    employee = models.ForeignKey(
        EmployeeProfile, on_delete=models.CASCADE, verbose_name="Сотрудник",
        db_column="employee_id",
    )
    type = models.CharField("Тип", max_length=10, choices=ADJUSTMENT_TYPE_CHOICES)
    amount = models.DecimalField("Сумма", max_digits=10, decimal_places=2)
    comment = models.TextField("Комментарий")
    date = models.DateField("Дата")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        managed = False
        db_table = "adjustment"
        verbose_name = "Премия / Штраф"
        verbose_name_plural = "Премии и штрафы"

    def __str__(self):
        return f"{self.get_type_display()}: {self.amount} ({self.employee})"


class QRSession(models.Model):
    token = models.UUIDField("Токен", unique=True)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, verbose_name="Компания",
        db_column="company_id",
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    expires_at = models.DateTimeField("Истекает")
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        managed = False
        db_table = "qr_session"
        verbose_name = "QR-сессия"
        verbose_name_plural = "QR-сессии"

    def __str__(self):
        return f"QR {self.token} ({self.company})"


class TimeEntry(models.Model):
    employee = models.ForeignKey(
        EmployeeProfile, on_delete=models.CASCADE, verbose_name="Сотрудник",
        db_column="employee_id",
    )
    date = models.DateField("Дата")
    check_in = models.DateTimeField("Вход")
    check_out = models.DateTimeField("Выход", null=True, blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        managed = False
        db_table = "time_entry"
        verbose_name = "Запись рабочего времени"
        verbose_name_plural = "Записи рабочего времени"

    def __str__(self):
        return f"{self.employee} — {self.date}"
