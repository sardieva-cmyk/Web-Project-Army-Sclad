import os
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings # Нужно для путей

# Импорты для ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics # <--- ВАЖНО
from reportlab.pdfbase.ttfonts import TTFont # <--- ВАЖНО

import xlsxwriter
from io import BytesIO
from .models import Weapon, Ammunition
from datetime import datetime

@login_required(login_url='/login/')
def dashboard(request):
    weapons = Weapon.objects.all()
    ammo = Ammunition.objects.first() or Ammunition.objects.create(quantity=400000)
    critical_weapons = weapons.filter(quantity__lte=F('critical_threshold'))
    total_weapons = weapons.aggregate(total=Sum('quantity'))['total'] or 0

    context = {
        'weapons': weapons,
        'ammo': ammo,
        'critical_weapons': critical_weapons,
        'total_weapons': total_weapons,
    }
    return render(request, 'warehouse/dashboard.html', context)

@login_required
def export_excel(request):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Оружие')

    header = ['Модель', 'Категория', 'Поставщик', 'Остаток', 'Критический порог', 'Статус']
    worksheet.write_row(0, 0, header)

    row = 1
    for w in Weapon.objects.all():
        status = "В наличии" if w.quantity > w.critical_threshold else "КРИТИЧЕСКИ МАЛО!"
        worksheet.write_row(row, 0, [
            w.model, w.category.name, str(w.supplier or "—"), w.quantity, w.critical_threshold, status
        ])
        row += 1

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="Военный_склад_{datetime.now().strftime("%d%m%Y")}.xlsx"'
    return response

@login_required
def export_pdf(request):
    weapons = Weapon.objects.all()
    ammo = Ammunition.objects.first() or Ammunition.objects.create(quantity=400000)

    # 1. Попытка через WeasyPrint (HTML -> PDF)
    # Это сработает, только если у вас установлен GTK3 в системе.
    try:
        from weasyprint import HTML
        html_string = render_to_string('warehouse/report_pdf.html', {
            'weapons': weapons,
            'ammo': ammo,
            'date': datetime.now().strftime('%d.%m.%Y'),
            'time': datetime.now().strftime('%H:%M'),
        })
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Отчёт_склада_{datetime.now().strftime("%d%m%Y")}.pdf"'
        return response
    
    except Exception as e:
        # Если WeasyPrint нет, выводим ошибку в консоль сервера, чтобы вы знали
        print(f"WeasyPrint error: {e}. Switching to ReportLab fallback.")

    # 2. Fallback на ReportLab (Python генератор)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # --- НАСТРОЙКА ШРИФТОВ ДЛЯ РУССКОГО ЯЗЫКА ---
    # Пытаемся зарегистрировать Arial. Если вы на Windows, это сработает сразу.
    # Если на Linux/Mac, возможно, придется указать путь к файлу .ttf
    try:
        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        font_name = 'Arial'
    except:
        # Если arial.ttf не найден системой, нужен запасной план
        # (в реальном проекте лучше положить файл шрифта в папку static)
        font_name = 'Helvetica' # Русский текст будет квадратиками, но файл скачается
    
    styles = getSampleStyleSheet()
    # Создаем свой стиль для заголовка с русским шрифтом
    style_title = ParagraphStyle(
        'RussianTitle', 
        parent=styles['Title'], 
        fontName=font_name,
        fontSize=18,
        spaceAfter=14
    )
    # Стиль для обычного текста
    style_normal = ParagraphStyle(
        'RussianNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10
    )

    story = []
    story.append(Paragraph('Отчёт: Военный склад', style_title))
    story.append(Paragraph(f'Дата: {datetime.now().strftime("%d.%m.%Y %H:%M")}', style_normal))
    story.append(Spacer(1, 12))

    # Заголовки таблицы
    data = [['Модель', 'Категория', 'Поставщик', 'Остаток', 'Статус']]
    
    for w in weapons:
        status = 'В наличии' if w.quantity > w.critical_threshold else 'МАЛО!'
        # str(...) нужен, чтобы избежать ошибок типов
        data.append([
            str(w.model), 
            str(w.category.name if w.category else '-'), 
            str(w.supplier or '—'), 
            str(w.quantity), 
            status
        ])

    table = Table(data, hAlign='LEFT')
    
    # Стили таблицы тоже должны использовать шрифт
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name), # <--- Применяем шрифт ко всей таблице
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff4444')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))

    story.append(table)
    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Отчёт_ReportLab_{datetime.now().strftime("%d%m%Y")}.pdf"'
    return response