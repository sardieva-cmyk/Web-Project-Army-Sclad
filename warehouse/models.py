from django.db import models
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

User = get_user_model()

# Категории оружия
class WeaponCategory(models.Model):
    CATEGORY_CHOICES = [
        ('ШВ', 'Штурмовые винтовки'),
        ('ПП', 'Пистолеты-пулемёты'),
        ('РП', 'Ручные пулемёты'),
        ('СВ', 'Снайперские винтовки'),
    ]
    
    code = models.CharField(max_length=2, choices=CATEGORY_CHOICES, unique=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.code} — {self.name}"

    class Meta:
        verbose_name = "Категория оружия"
        verbose_name_plural = "Категории оружия"


# Поставщики
class Supplier(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=50, blank=True)
    contact_email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"


# Оружие
class Weapon(models.Model):
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=50)  # Например: АК-74, M16A4
    category = models.ForeignKey(WeaponCategory, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0, verbose_name="Остаток на складе")
    critical_threshold = models.PositiveIntegerField(default=5000, help_text="При каком остатке слать тревогу")

    def __str__(self):
        return f"{self.model} ({self.category.code})"

    def save(self, *args, **kwargs):
        old = None
        if self.pk:
            old = Weapon.objects.get(pk=self.pk).quantity

        super().save(*args, **kwargs)

        # Уведомление при падении ниже критического уровня
        if self.quantity <= self.critical_threshold:
            if old is None or old > self.critical_threshold:
                self.send_critical_alert()

    def send_critical_alert(self):
        subject = "ВНИМАНИЕ! Критический остаток оружия!"
        message = f"""
        ТРЕВОГА НА ВОЕННОМ СКЛАДЕ!

        Оружие: {self.model}
        Категория: {self.category}
        Остаток: {self.quantity} шт.
        Критический порог: {self.critical_threshold} шт.

        ТРЕБУЕТСЯ СРОЧНОЕ ПОПОЛНЕНИЕ!
        """
        send_mail(
            subject,
            message,
            'sklad@voenny.ru',
            ['commander@voenny.ru', 'logist@voenny.ru'],
            fail_silently=False,
        )

    class Meta:
        verbose_name = "Оружие"
        verbose_name_plural = "Оружие"


# Боеприпасы (отдельно — как ты и хотел)
class Ammunition(models.Model):
    name = models.CharField(max_length=100, default="Боеприпасы универсальные")
    quantity = models.PositiveBigIntegerField(default=400000, verbose_name="Общий остаток")
    monthly_incoming = models.PositiveIntegerField(default=200000, help_text="Поступает в месяц")
    monthly_outgoing = models.PositiveIntegerField(default=350000, help_text="Расход в месяц")
    critical_threshold = models.PositiveIntegerField(default=100000, help_text="Критический минимум")

    def __str__(self):
        return f"Боеприпасы — {self.quantity:,} шт."

    def save(self, *args, **kwargs):
        old = None
        if self.pk:
            old = Ammunition.objects.get(pk=self.pk).quantity

        super().save(*args, **kwargs)

        if self.quantity <= self.critical_threshold:
            if old is None or old > self.critical_threshold:
                self.send_ammo_alert()

    def send_ammo_alert(self):
        subject = "КРИТИЧЕСКИ МАЛО БОЕПРИПАСОВ!"
        message = f"""
        ВНИМАНИЕ! КРИТИЧЕСКИЙ ОСТАТОК БОЕПРИПАСОВ!

        Остаток: {self.quantity:,} патронов
        Критический порог: {self.critical_threshold:,}
        Ежемесячный приход: {self.monthly_incoming:,}
        Ежемесячный расход: {self.monthly_outgoing:,}

        СРОЧНО ЗАКАЗАТЬ ПОСТАВКУ!
        """
        send_mail(
            subject,
            message,
            'sklad@voenny.ru',
            ['general@voenny.ru'],
            fail_silently=False,
        )

    class Meta:
        verbose_name = "Боеприпасы"
        verbose_name_plural = "Боеприпасы"