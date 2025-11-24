from django.shortcuts import render
from django.db.models import Sum, F   # ← это уже есть
from .models import Weapon, Ammunition


def dashboard(request):
    weapons = Weapon.objects.all()
    ammo = Ammunition.objects.first() or Ammunition.objects.create()  # создастся, если ещё нет
    critical_weapons = weapons.filter(quantity__lte=F('critical_threshold'))
    total_weapons = weapons.aggregate(total=Sum('quantity'))['total'] or 0

    context = {
        'weapons': weapons,
        'ammo': ammo,
        'critical_weapons': critical_weapons,
        'total_weapons': total_weapons,
    }
    return render(request, 'warehouse/dashboard.html', context)