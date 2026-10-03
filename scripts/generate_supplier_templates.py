from __future__ import annotations

import csv
import html
import hashlib
import sys
from pathlib import Path
from string import Template

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
  sys.path.insert(0, str(PROJECT_ROOT))

from supplier_template_specs import (
    layout_variant_for_supplier,
    supplier_profile_for_supplier,
    supplier_slug,
)

SUPPLIERS_CSV = PROJECT_ROOT / "data" / "suppliers.csv"
TEMPLATES_DIR = PROJECT_ROOT / "templates" / "suppliers"


TABLE_BLOCK = """
    <table class="$table_class">
      <thead>
        <tr>
          {% for column in supplier_profile.column_order %}
            <th>{{ column }}</th>
          {% endfor %}
        </tr>
      </thead>
      <tbody>
      {% for row in products %}
        {% if row.is_merged_row %}
          <tr class="merged-row">
            <td colspan="{{ supplier_profile.column_order|length }}"><strong>{{ row.designation }}</strong></td>
          </tr>
        {% else %}
          <tr style="transform: translateX({{ row.offset_px }}px)">
            {% for column in supplier_profile.column_order %}
              {% if column == 'designation' %}<td>{{ row.designation }}</td>{% endif %}
              {% if column == 'code' %}<td class="c">{{ row.code_produit if row.code_produit is not none else '' }}</td>{% endif %}
              {% if column == 'qty' %}<td class="c">{{ row.qty if row.qty is not none else '' }}</td>{% endif %}
              {% if column == 'unit_price' %}<td class="r">{{ "%.2f"|format(row.unit_price) if row.unit_price is not none else '' }}</td>{% endif %}
              {% if column == 'pph' %}<td class="r">{{ "%.2f"|format(row.pph) if row.pph is not none else '' }}</td>{% endif %}
              {% if column == 'tva' %}<td class="c">{{ (row.tva * 100)|int if row.tva is not none else '' }}%</td>{% endif %}
              {% if column == 'lot' %}<td class="c">{{ row.lot if row.lot is not none else '' }}</td>{% endif %}
              {% if column == 'peremption' %}<td class="c">{{ row.peremption if row.peremption is not none else '' }}</td>{% endif %}
              {% if column == 'remise' %}<td class="c">{{ row.remise if row.remise is not none else '' }}</td>{% endif %}
              {% if column == 'line_total' %}<td class="r">{{ "%.2f"|format(row.line_total) if row.line_total is not none else '' }}</td>{% endif %}
            {% endfor %}
          </tr>
        {% endif %}
      {% endfor %}
      </tbody>
    </table>
""".rstrip()


NOTES_BLOCK = """
    <div class="notes">
      {% for note in notes %}<div>{{ note }}</div>{% endfor %}
    </div>
""".rstrip()


TOTALS_BLOCK = """
    <table class="totals">
      <tr><td><strong>{{ supplier_profile.totals_labels[0] }}</strong></td><td class="r">{{ "%.2f"|format(totals.ht) }}</td></tr>
      <tr><td><strong>{{ supplier_profile.totals_labels[1] }}</strong></td><td class="r">{{ "%.2f"|format(totals.tva) }}</td></tr>
      <tr><td><strong>{{ supplier_profile.totals_labels[2] }}</strong></td><td class="r"><strong>{{ "%.2f"|format(totals.ttc) }} {{ currency }}</strong></td></tr>
    </table>
""".rstrip()


LAYOUTS = {
    "ledger": Template(
        """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <style>
    body { margin: 0; background: $page_bg; font-family: $font_family; }
    .page { width: $page_width; min-height: $page_height; margin: 26px auto; background: #fff; border: 2px solid $border_color; box-shadow: 0 12px 22px rgba(28, 44, 76, 0.12); box-sizing: border-box; overflow: hidden; }
    .band { background: linear-gradient(90deg, $header_color, $accent_color); color: #fff; padding: 18px 22px; display: grid; grid-template-columns: 1.3fr 1fr; gap: 14px; }
    .band h1 { margin: 0; font-size: 31px; letter-spacing: 0.8px; }
    .band .supplier { text-align: right; font-size: 12px; line-height: 1.4; }
    .meta { padding: 12px 18px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; border-bottom: 1px solid $border_color; font-size: 12px; }
    .meta .cell { border: 1px solid $border_color; padding: 7px; min-height: 34px; }
    .content { padding: 12px 12px 14px 12px; }
    .table-wrap { overflow: hidden; }
    .doc-table { width: 100%; border-collapse: collapse; font-size: 12px; background: $table_bg; }
    .doc-table th, .doc-table td { border: 1px solid $border_color; padding: 5px 6px; }
    .doc-table th { background: $table_head_bg; text-transform: uppercase; font-size: 11px; }
    .doc-table tbody tr:nth-child(odd) td { background: $table_alt_bg; }
    .merged-row td { background: #f0f5fb; }
    .c { text-align: center; }
    .r { text-align: right; }
    .footer-grid { margin-top: 12px; display: grid; grid-template-columns: 1fr 320px; gap: 10px; }
    .notes { border: 1px dashed $border_color; background: $footer_bg; padding: 10px; font-size: 12px; line-height: 1.35; }
    .totals { width: 100%; border-collapse: collapse; font-size: 13px; }
    .totals td { border: 1px solid $border_color; padding: 7px; }
    .stamp { position: absolute; right: 46px; top: 145px; width: 100px; height: 100px; border: 2px solid rgba(160, 30, 30, 0.35); border-radius: 50%; color: rgba(160, 30, 30, 0.45); display: {% if show_stamp %}flex{% else %}none{% endif %}; align-items: center; justify-content: center; transform: rotate(-16deg); font-weight: 700; }
    .signature { display: {% if show_signature %}block{% else %}none{% endif %}; text-align: right; font-style: italic; font-size: 20px; color: $header_color; transform: rotate(-6deg); margin-top: 8px; }
  </style>
</head>
<body>
  <div class="page" data-template="$supplier_slug">
    <div class="stamp">RECU</div>
    <div class="band">
      <div>
        <h1>{{ supplier_profile.title }}</h1>
        <div><strong>BL:</strong> {{ bl_number }}</div>
        <div><strong>Layout:</strong> $layout_label</div>
      </div>
      <div class="supplier">
        <div><strong>{{ supplier.name }}</strong></div>
        <div>{{ supplier.address }}</div>
        <div>{{ supplier.phone }}</div>
        <div>{{ supplier.city }}</div>
      </div>
    </div>
    <div class="meta">
      <div class="cell"><strong>Date</strong><br>{{ issue_date }}</div>
      <div class="cell"><strong>Client</strong><br>{{ client_name }}</div>
      <div class="cell"><strong>Code</strong><br>{{ client_code }}</div>
      <div class="cell"><strong>Adresse</strong><br>{{ client_address }}</div>
    </div>
    <div class="content">
$TABLE_BLOCK
      <div class="footer-grid">
$NOTES_BLOCK
$TOTALS_BLOCK
      </div>
      <div class="signature">cachet et signature</div>
    </div>
  </div>
</body>
</html>
""".replace("$TABLE_BLOCK", TABLE_BLOCK).replace("$NOTES_BLOCK", NOTES_BLOCK).replace("$TOTALS_BLOCK", TOTALS_BLOCK)
    ),
    "clinical": Template(
        """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <style>
    body { margin: 0; background: $page_bg; font-family: $font_family; }
    .page { width: $page_width; min-height: $page_height; margin: 28px auto; background: #fff; border: 1px solid $border_color; box-shadow: 0 14px 24px rgba(26, 68, 78, 0.10); box-sizing: border-box; overflow: hidden; }
    .hero { display: grid; grid-template-columns: 84px 1.4fr 1fr; gap: 16px; padding: 16px 20px; background: linear-gradient(90deg, $header_color, $accent_color); color: #fff; }
    .badge { border: 1px dashed rgba(255,255,255,0.7); display: flex; align-items: center; justify-content: center; font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; }
    .hero h1 { margin: 0; font-size: 28px; }
    .hero .supplier { text-align: right; font-size: 12px; line-height: 1.4; }
    .meta { padding: 12px 18px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; border-bottom: 1px solid $border_color; font-size: 12px; }
    .meta .cell { border: 1px solid $border_color; padding: 7px; min-height: 34px; }
    .content { padding: 12px 12px 14px 12px; }
    .doc-table { width: 100%; border-collapse: collapse; font-size: 11.5px; background: $table_bg; }
    .doc-table th, .doc-table td { border-bottom: 1px solid $border_color; padding: 5px 6px; }
    .doc-table th { background: $table_head_bg; text-transform: uppercase; font-size: 10.5px; }
    .doc-table tbody tr:nth-child(odd) td { background: $table_alt_bg; }
    .merged-row td { background: #edf7fb; }
    .c { text-align: center; }
    .r { text-align: right; }
    .footer { margin-top: 12px; display: grid; grid-template-columns: 1.15fr 1fr; gap: 10px; }
    .notes { border: 1px dashed $border_color; background: $footer_bg; padding: 10px; font-size: 12px; line-height: 1.35; }
    .totals { width: 100%; border-collapse: collapse; font-size: 13px; }
    .totals td { border: 1px solid $border_color; padding: 7px; }
    .stamp { position: absolute; right: 34px; top: 138px; width: 92px; height: 92px; border: 2px solid rgba(26, 104, 125, 0.32); border-radius: 50%; color: rgba(26, 104, 125, 0.40); display: {% if show_stamp %}flex{% else %}none{% endif %}; align-items: center; justify-content: center; transform: rotate(-15deg); font-weight: 700; }
    .signature { display: {% if show_signature %}block{% else %}none{% endif %}; margin-top: 8px; color: $header_color; font-style: italic; text-align: right; font-size: 19px; transform: rotate(-5deg); }
  </style>
</head>
<body>
  <div class="page" data-template="$supplier_slug">
    <div class="stamp">LOT</div>
    <div class="hero">
      <div class="badge">$layout_label</div>
      <div>
        <h1>{{ supplier_profile.title }}</h1>
        <div><strong>BL:</strong> {{ bl_number }}</div>
      </div>
      <div class="supplier">
        <div><strong>{{ supplier.name }}</strong></div>
        <div>{{ supplier.address }}</div>
        <div>{{ supplier.phone }}</div>
        <div>{{ supplier.city }}</div>
      </div>
    </div>
    <div class="meta">
      <div class="cell"><strong>Date</strong><br>{{ issue_date }}</div>
      <div class="cell"><strong>Client</strong><br>{{ client_name }}</div>
      <div class="cell"><strong>Code</strong><br>{{ client_code }}</div>
      <div class="cell"><strong>Adresse</strong><br>{{ client_address }}</div>
    </div>
    <div class="content">
$TABLE_BLOCK
      <div class="footer">
$NOTES_BLOCK
$TOTALS_BLOCK
      </div>
      <div class="signature">suivi lot et peremption</div>
    </div>
  </div>
</body>
</html>
""".replace("$TABLE_BLOCK", TABLE_BLOCK).replace("$NOTES_BLOCK", NOTES_BLOCK).replace("$TOTALS_BLOCK", TOTALS_BLOCK)
    ),
    "receipt": Template(
        """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <style>
    body { margin: 0; background: $page_bg; font-family: $font_family; }
    .ticket { width: $page_width; min-height: $page_height; margin: 24px auto; background: #fff; border: 1px dashed $border_color; box-shadow: 0 8px 18px rgba(88, 70, 38, 0.10); box-sizing: border-box; padding: 16px 12px; }
    .top { text-align: center; border-bottom: 1px dashed $border_color; padding-bottom: 10px; }
    .top .logo { margin: 0 auto 6px auto; width: 144px; height: 34px; line-height: 34px; border: 1px dashed $accent_color; font-size: 10px; color: $header_color; }
    .top h1 { margin: 0; font-size: 26px; color: $header_color; }
    .supplier { margin-top: 6px; font-size: 12px; line-height: 1.3; }
    .meta { font-size: 11px; border-top: 1px dashed $border_color; border-bottom: 1px dashed $border_color; padding: 7px 0; margin: 8px 0; }
    .meta .row { display: flex; justify-content: space-between; margin: 2px 0; }
    .doc-table { width: 100%; border-collapse: collapse; font-size: 10.8px; background: $table_bg; }
    .doc-table th, .doc-table td { border-bottom: 1px dotted $border_color; padding: 3px 2px; }
    .doc-table th { background: $table_head_bg; text-align: left; text-transform: uppercase; font-size: 10px; }
    .doc-table tbody tr:nth-child(odd) td { background: $table_alt_bg; }
    .merged-row td { background: #fcf4e9; }
    .c { text-align: center; }
    .r { text-align: right; }
    .footer { margin-top: 10px; border-top: 1px dashed $border_color; padding-top: 8px; display: grid; grid-template-columns: 1fr; gap: 10px; }
    .notes { font-size: 11px; }
    .totals { width: 100%; border-collapse: collapse; font-size: 12px; }
    .totals td { border: 1px solid $border_color; padding: 6px; }
    .stamp { position: absolute; right: 24px; top: 138px; width: 96px; height: 96px; border: 2px solid rgba(109, 74, 43, 0.35); border-radius: 50%; color: rgba(109, 74, 43, 0.44); display: {% if show_stamp %}flex{% else %}none{% endif %}; align-items: center; justify-content: center; transform: rotate(-18deg); font-weight: 700; }
    .signature { display: {% if show_signature %}block{% else %}none{% endif %}; text-align: right; color: $header_color; font-style: italic; font-size: 18px; transform: rotate(-6deg); }
  </style>
</head>
<body>
  <div class="ticket" data-template="$supplier_slug">
    <div class="stamp">CTRL</div>
    <div class="top">
      <div class="logo">$layout_label</div>
      <h1>{{ supplier_profile.title }}</h1>
      <div class="supplier">
        <div><strong>{{ supplier.name }}</strong></div>
        <div>{{ supplier.address }}</div>
        <div>{{ supplier.phone }}</div>
        <div>{{ supplier.city }}</div>
      </div>
    </div>
    <div class="meta">
      <div class="row"><span>BL</span><span>{{ bl_number }}</span></div>
      <div class="row"><span>Date</span><span>{{ issue_date }}</span></div>
      <div class="row"><span>Client</span><span>{{ client_name }}</span></div>
      <div class="row"><span>Code</span><span>{{ client_code }}</span></div>
    </div>
$TABLE_BLOCK
    <div class="footer">
$NOTES_BLOCK
$TOTALS_BLOCK
      <div class="signature">controle reception</div>
    </div>
  </div>
</body>
</html>
""".replace("$TABLE_BLOCK", TABLE_BLOCK).replace("$NOTES_BLOCK", NOTES_BLOCK).replace("$TOTALS_BLOCK", TOTALS_BLOCK)
    ),
    "invoice": Template(
        """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <style>
    body { margin: 0; background: $page_bg; font-family: $font_family; }
    .sheet { width: $page_width; min-height: $page_height; margin: 26px auto; background: #fff; border: 1px solid $border_color; box-shadow: 0 14px 24px rgba(74, 45, 109, 0.10); box-sizing: border-box; overflow: hidden; }
    .header { background: linear-gradient(90deg, $header_color, $accent_color); color: #fff; padding: 18px 22px; display: grid; grid-template-columns: 1.25fr 1fr; gap: 14px; }
    .header h1 { margin: 0; font-size: 30px; }
    .supplier { text-align: right; font-size: 12px; line-height: 1.35; }
    .meta { padding: 12px 18px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; border-bottom: 1px solid $border_color; font-size: 12px; }
    .meta .cell { border: 1px solid $border_color; padding: 7px; min-height: 34px; }
    .content { padding: 12px; }
    .table-box { border: 1px solid $border_color; background: $table_bg; }
    .doc-table { width: 100%; border-collapse: collapse; font-size: 11.5px; }
    .doc-table th, .doc-table td { border-bottom: 1px solid $border_color; padding: 5px 6px; }
    .doc-table th { background: $table_head_bg; text-transform: uppercase; font-size: 10.5px; }
    .doc-table tbody tr:nth-child(odd) td { background: $table_alt_bg; }
    .merged-row td { background: #f4ecfb; }
    .c { text-align: center; }
    .r { text-align: right; }
    .lower { margin-top: 12px; display: grid; grid-template-columns: 1fr 320px; gap: 10px; }
    .notes { border: 1px dashed $border_color; background: $footer_bg; padding: 10px; font-size: 12px; line-height: 1.35; }
    .totals { width: 100%; border-collapse: collapse; font-size: 13px; }
    .totals td { border: 1px solid $border_color; padding: 7px; }
    .signature { display: {% if show_signature %}block{% else %}none{% endif %}; margin-top: 8px; color: $header_color; font-style: italic; font-size: 19px; text-align: right; transform: rotate(-5deg); }
  </style>
</head>
<body>
  <div class="sheet" data-template="$supplier_slug">
    <div class="header">
      <div>
        <h1>{{ supplier_profile.title }}</h1>
        <div><strong>BL:</strong> {{ bl_number }}</div>
        <div>Facturation detaillee</div>
      </div>
      <div class="supplier">
        <div><strong>{{ supplier.name }}</strong></div>
        <div>{{ supplier.address }}</div>
        <div>{{ supplier.phone }}</div>
        <div>{{ supplier.city }}</div>
      </div>
    </div>
    <div class="meta">
      <div class="cell"><strong>Date</strong><br>{{ issue_date }}</div>
      <div class="cell"><strong>Client</strong><br>{{ client_name }}</div>
      <div class="cell"><strong>Code</strong><br>{{ client_code }}</div>
      <div class="cell"><strong>Adresse</strong><br>{{ client_address }}</div>
    </div>
    <div class="content">
      <div class="table-box">
$TABLE_BLOCK
      </div>
      <div class="lower">
$NOTES_BLOCK
$TOTALS_BLOCK
      </div>
      <div class="signature">remise contractuelle appliquee</div>
    </div>
  </div>
</body>
</html>
""".replace("$TABLE_BLOCK", TABLE_BLOCK).replace("$NOTES_BLOCK", NOTES_BLOCK).replace("$TOTALS_BLOCK", TOTALS_BLOCK)
    ),
    "dossier": Template(
        """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <style>
    body { margin: 0; background: $page_bg; font-family: $font_family; }
    .sheet { width: $page_width; min-height: $page_height; margin: 24px auto; background: #fff; border: 2px solid $border_color; box-sizing: border-box; overflow: hidden; }
    .top { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 18px 20px 12px 20px; background: linear-gradient(90deg, $header_color, $accent_color); color: #fff; }
    .top h1 { margin: 0; font-size: 29px; }
    .supplier { text-align: right; font-size: 12px; line-height: 1.35; }
    .meta { padding: 12px 18px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; border-bottom: 1px solid $border_color; font-size: 12px; }
    .meta .cell { border: 1px solid $border_color; padding: 7px; min-height: 34px; }
    .content { padding: 12px; }
    .doc-table { width: 100%; border-collapse: collapse; font-size: 11.5px; background: $table_bg; }
    .doc-table th, .doc-table td { border: 1px solid $border_color; padding: 5px 6px; }
    .doc-table th { background: $table_head_bg; text-transform: uppercase; font-size: 10.5px; }
    .doc-table tbody tr:nth-child(odd) td { background: $table_alt_bg; }
    .merged-row td { background: #edf7f0; }
    .c { text-align: center; }
    .r { text-align: right; }
    .bottom { margin-top: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .notes { border: 1px dashed $border_color; background: $footer_bg; padding: 10px; font-size: 12px; line-height: 1.35; }
    .totals { width: 100%; border-collapse: collapse; font-size: 13px; }
    .totals td { border: 1px solid $border_color; padding: 7px; }
    .signature { display: {% if show_signature %}block{% else %}none{% endif %}; text-align: right; color: $header_color; font-style: italic; font-size: 18px; transform: rotate(-5deg); }
  </style>
</head>
<body>
  <div class="sheet" data-template="$supplier_slug">
    <div class="top">
      <div>
        <h1>{{ supplier_profile.title }}</h1>
        <div><strong>BL:</strong> {{ bl_number }}</div>
        <div>Version dossier administratif</div>
      </div>
      <div class="supplier">
        <div><strong>{{ supplier.name }}</strong></div>
        <div>{{ supplier.address }}</div>
        <div>{{ supplier.phone }}</div>
        <div>{{ supplier.city }}</div>
      </div>
    </div>
    <div class="meta">
      <div class="cell"><strong>Date</strong><br>{{ issue_date }}</div>
      <div class="cell"><strong>Client</strong><br>{{ client_name }}</div>
      <div class="cell"><strong>Code</strong><br>{{ client_code }}</div>
      <div class="cell"><strong>Adresse</strong><br>{{ client_address }}</div>
    </div>
    <div class="content">
$TABLE_BLOCK
      <div class="bottom">
$NOTES_BLOCK
$TOTALS_BLOCK
      </div>
      <div class="signature">suivi code produit et peremption</div>
    </div>
  </div>
</body>
</html>
""".replace("$TABLE_BLOCK", TABLE_BLOCK).replace("$NOTES_BLOCK", NOTES_BLOCK).replace("$TOTALS_BLOCK", TOTALS_BLOCK)
    ),
    "executive": Template(
        """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <style>
    body { margin: 0; background: $page_bg; font-family: $font_family; }
    .sheet { width: $page_width; min-height: $page_height; margin: 24px auto; background: #fff; border: 1px solid $border_color; box-shadow: 0 14px 24px rgba(41, 48, 63, 0.12); box-sizing: border-box; overflow: hidden; }
    .band { background: linear-gradient(90deg, $header_color, $accent_color); color: #fff; padding: 18px 22px; display: grid; grid-template-columns: 1.3fr 1fr; gap: 14px; }
    .band h1 { margin: 0; font-size: 30px; }
    .supplier { text-align: right; font-size: 12px; line-height: 1.35; }
    .meta { padding: 12px 18px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; border-bottom: 1px solid $border_color; font-size: 12px; }
    .meta .cell { border: 1px solid $border_color; padding: 7px; min-height: 34px; }
    .content { padding: 12px; }
    .layout { display: grid; grid-template-columns: 1fr 280px; gap: 10px; align-items: start; }
    .doc-table { width: 100%; border-collapse: collapse; font-size: 11.5px; background: $table_bg; }
    .doc-table th, .doc-table td { border: 1px solid $border_color; padding: 5px 6px; }
    .doc-table th { background: $table_head_bg; text-transform: uppercase; font-size: 10.5px; }
    .doc-table tbody tr:nth-child(odd) td { background: $table_alt_bg; }
    .merged-row td { background: #f2f3f7; }
    .c { text-align: center; }
    .r { text-align: right; }
    .panel { border: 1px solid $border_color; background: $footer_bg; padding: 10px; }
    .notes { font-size: 12px; line-height: 1.35; }
    .totals { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .totals td { border: 1px solid $border_color; padding: 7px; }
    .signature { display: {% if show_signature %}block{% else %}none{% endif %}; margin-top: 10px; color: $header_color; font-style: italic; font-size: 18px; text-align: right; transform: rotate(-6deg); }
  </style>
</head>
<body>
  <div class="sheet" data-template="$supplier_slug">
    <div class="band">
      <div>
        <h1>{{ supplier_profile.title }}</h1>
        <div><strong>BL:</strong> {{ bl_number }}</div>
        <div>Bloc executif structuré</div>
      </div>
      <div class="supplier">
        <div><strong>{{ supplier.name }}</strong></div>
        <div>{{ supplier.address }}</div>
        <div>{{ supplier.phone }}</div>
        <div>{{ supplier.city }}</div>
      </div>
    </div>
    <div class="meta">
      <div class="cell"><strong>Date</strong><br>{{ issue_date }}</div>
      <div class="cell"><strong>Client</strong><br>{{ client_name }}</div>
      <div class="cell"><strong>Code</strong><br>{{ client_code }}</div>
      <div class="cell"><strong>Adresse</strong><br>{{ client_address }}</div>
    </div>
    <div class="content">
      <div class="layout">
$TABLE_BLOCK
        <div class="panel">
$NOTES_BLOCK
$TOTALS_BLOCK
        </div>
      </div>
      <div class="signature">validation cadre direction</div>
    </div>
  </div>
</body>
</html>
""".replace("$TABLE_BLOCK", TABLE_BLOCK).replace("$NOTES_BLOCK", NOTES_BLOCK).replace("$TOTALS_BLOCK", TOTALS_BLOCK)
    ),
    "compact": Template(
        """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <style>
    body { margin: 0; background: $page_bg; font-family: $font_family; }
    .sheet { width: $page_width; min-height: $page_height; margin: 28px auto; background: #fff; border: 1px solid $border_color; box-sizing: border-box; overflow: hidden; }
    .top { background: linear-gradient(90deg, $header_color, $accent_color); color: #fff; padding: 14px 18px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .top h1 { margin: 0; font-size: 26px; }
    .supplier { text-align: right; font-size: 12px; line-height: 1.35; }
    .meta { padding: 10px 14px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; border-bottom: 1px solid $border_color; font-size: 12px; }
    .meta .cell { border: 1px solid $border_color; padding: 6px; min-height: 32px; }
    .content { padding: 10px 10px 12px 10px; }
    .doc-table { width: 100%; border-collapse: collapse; font-size: 10.8px; background: $table_bg; }
    .doc-table th, .doc-table td { border-bottom: 1px dotted $border_color; padding: 3px 4px; }
    .doc-table th { background: $table_head_bg; text-transform: uppercase; font-size: 10px; }
    .doc-table tbody tr:nth-child(odd) td { background: $table_alt_bg; }
    .merged-row td { background: #f5efef; }
    .c { text-align: center; }
    .r { text-align: right; }
    .footer { margin-top: 10px; border-top: 1px dashed $border_color; padding-top: 8px; }
    .notes { font-size: 11px; line-height: 1.35; }
    .totals { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; }
    .totals td { border: 1px solid $border_color; padding: 6px; }
  </style>
</head>
<body>
  <div class="sheet" data-template="$supplier_slug">
    <div class="top">
      <div>
        <h1>{{ supplier_profile.title }}</h1>
        <div><strong>BL:</strong> {{ bl_number }}</div>
      </div>
      <div class="supplier">
        <div><strong>{{ supplier.name }}</strong></div>
        <div>{{ supplier.address }}</div>
        <div>{{ supplier.phone }}</div>
        <div>{{ supplier.city }}</div>
      </div>
    </div>
    <div class="meta">
      <div class="cell"><strong>Date</strong><br>{{ issue_date }}</div>
      <div class="cell"><strong>Client</strong><br>{{ client_name }}</div>
      <div class="cell"><strong>Code</strong><br>{{ client_code }}</div>
      <div class="cell"><strong>Adresse</strong><br>{{ client_address }}</div>
    </div>
    <div class="content">
$TABLE_BLOCK
      <div class="footer">
$NOTES_BLOCK
$TOTALS_BLOCK
      </div>
    </div>
  </div>
</body>
</html>
""".replace("$TABLE_BLOCK", TABLE_BLOCK).replace("$NOTES_BLOCK", NOTES_BLOCK).replace("$TOTALS_BLOCK", TOTALS_BLOCK)
    ),
    "technical": Template(
        """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <style>
    body { margin: 0; background: $page_bg; font-family: $font_family; }
    .sheet { width: $page_width; min-height: $page_height; margin: 26px auto; background: #fff; border: 1px solid $border_color; box-sizing: border-box; overflow: hidden; }
    .top { background: linear-gradient(90deg, $header_color, $accent_color); color: #fff; padding: 16px 18px; display: grid; grid-template-columns: 1.1fr 1fr; gap: 12px; }
    .top h1 { margin: 0; font-size: 27px; }
    .supplier { text-align: right; font-size: 12px; line-height: 1.35; }
    .meta { padding: 10px 14px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; border-bottom: 1px solid $border_color; font-size: 12px; }
    .meta .cell { border: 1px solid $border_color; padding: 6px; min-height: 32px; }
    .content { padding: 10px 10px 12px 10px; }
    .doc-table { width: 100%; border-collapse: collapse; font-size: 11px; background: $table_bg; }
    .doc-table th, .doc-table td { border: 1px solid $border_color; padding: 4px 5px; }
    .doc-table th { background: $table_head_bg; text-transform: uppercase; font-size: 10px; }
    .doc-table tbody tr:nth-child(odd) td { background: $table_alt_bg; }
    .merged-row td { background: #eef6fa; }
    .c { text-align: center; }
    .r { text-align: right; }
    .bottom { margin-top: 10px; display: grid; grid-template-columns: 1fr 300px; gap: 10px; }
    .notes { border: 1px dashed $border_color; background: $footer_bg; padding: 10px; font-size: 11px; line-height: 1.35; }
    .totals { width: 100%; border-collapse: collapse; font-size: 12px; }
    .totals td { border: 1px solid $border_color; padding: 6px; }
    .signature { display: {% if show_signature %}block{% else %}none{% endif %}; text-align: right; color: $header_color; font-style: italic; font-size: 18px; transform: rotate(-5deg); }
  </style>
</head>
<body>
  <div class="sheet" data-template="$supplier_slug">
    <div class="top">
      <div>
        <h1>{{ supplier_profile.title }}</h1>
        <div><strong>BL:</strong> {{ bl_number }}</div>
        <div>Bloc technique et controle lot</div>
      </div>
      <div class="supplier">
        <div><strong>{{ supplier.name }}</strong></div>
        <div>{{ supplier.address }}</div>
        <div>{{ supplier.phone }}</div>
        <div>{{ supplier.city }}</div>
      </div>
    </div>
    <div class="meta">
      <div class="cell"><strong>Date</strong><br>{{ issue_date }}</div>
      <div class="cell"><strong>Client</strong><br>{{ client_name }}</div>
      <div class="cell"><strong>Code</strong><br>{{ client_code }}</div>
      <div class="cell"><strong>Adresse</strong><br>{{ client_address }}</div>
    </div>
    <div class="content">
$TABLE_BLOCK
      <div class="bottom">
$NOTES_BLOCK
$TOTALS_BLOCK
      </div>
      <div class="signature">controle qualite reception</div>
    </div>
  </div>
</body>
</html>
""".replace("$TABLE_BLOCK", TABLE_BLOCK).replace("$NOTES_BLOCK", NOTES_BLOCK).replace("$TOTALS_BLOCK", TOTALS_BLOCK)
    ),
    "premium": Template(
        """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <style>
    body { margin: 0; background: $page_bg; font-family: $font_family; }
    .sheet { width: $page_width; min-height: $page_height; margin: 24px auto; background: #fff; border: 1px solid $border_color; box-shadow: 0 14px 26px rgba(139, 102, 31, 0.12); box-sizing: border-box; overflow: hidden; }
    .band { background: linear-gradient(90deg, $header_color, $accent_color); color: #fff; padding: 18px 20px; display: grid; grid-template-columns: 1.2fr 1fr; gap: 12px; }
    .band h1 { margin: 0; font-size: 30px; }
    .supplier { text-align: right; font-size: 12px; line-height: 1.35; }
    .meta { padding: 12px 18px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; border-bottom: 1px solid $border_color; font-size: 12px; }
    .meta .cell { border: 1px solid $border_color; padding: 6px; min-height: 32px; }
    .content { padding: 12px; }
    .doc-table { width: 100%; border-collapse: collapse; font-size: 11.5px; background: $table_bg; }
    .doc-table th, .doc-table td { border-bottom: 1px solid $border_color; padding: 5px 6px; }
    .doc-table th { background: $table_head_bg; text-transform: uppercase; font-size: 10.5px; }
    .doc-table tbody tr:nth-child(odd) td { background: $table_alt_bg; }
    .merged-row td { background: #fbf2dc; }
    .c { text-align: center; }
    .r { text-align: right; }
    .footer { margin-top: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .notes { border: 1px dashed $border_color; background: $footer_bg; padding: 10px; font-size: 12px; line-height: 1.35; }
    .totals { width: 100%; border-collapse: collapse; font-size: 13px; }
    .totals td { border: 1px solid $border_color; padding: 7px; }
    .signature { display: {% if show_signature %}block{% else %}none{% endif %}; text-align: right; color: $header_color; font-style: italic; font-size: 18px; transform: rotate(-5deg); }
  </style>
</head>
<body>
  <div class="sheet" data-template="$supplier_slug">
    <div class="band">
      <div>
        <h1>{{ supplier_profile.title }}</h1>
        <div><strong>BL:</strong> {{ bl_number }}</div>
        <div>Presentation premium</div>
      </div>
      <div class="supplier">
        <div><strong>{{ supplier.name }}</strong></div>
        <div>{{ supplier.address }}</div>
        <div>{{ supplier.phone }}</div>
        <div>{{ supplier.city }}</div>
      </div>
    </div>
    <div class="meta">
      <div class="cell"><strong>Date</strong><br>{{ issue_date }}</div>
      <div class="cell"><strong>Client</strong><br>{{ client_name }}</div>
      <div class="cell"><strong>Code</strong><br>{{ client_code }}</div>
      <div class="cell"><strong>Adresse</strong><br>{{ client_address }}</div>
    </div>
    <div class="content">
$TABLE_BLOCK
      <div class="footer">
$NOTES_BLOCK
$TOTALS_BLOCK
      </div>
      <div class="signature">remise premium appliquee</div>
    </div>
  </div>
</body>
</html>
""".replace("$TABLE_BLOCK", TABLE_BLOCK).replace("$NOTES_BLOCK", NOTES_BLOCK).replace("$TOTALS_BLOCK", TOTALS_BLOCK)
    ),
}


def _page_dimensions(seed: int, base_width: int, base_height: int) -> tuple[str, str]:
    width = base_width + (seed % 140)
    height = base_height + ((seed >> 8) % 180)
    return f"{width}px", f"{height}px"


def build_template(supplier_name: str) -> str:
    profile = supplier_profile_for_supplier(supplier_name)
    variant = layout_variant_for_supplier(supplier_name)
    digest = hashlib.sha1(profile["palette_seed"].to_bytes(8, "big", signed=False)).hexdigest()
    page_width, page_height = _page_dimensions(profile["palette_seed"], 1040, 1450)
    font_family = [
        "Arial, sans-serif",
        "Calibri, sans-serif",
        "Verdana, sans-serif",
        "Tahoma, sans-serif",
        "Georgia, serif",
        "Trebuchet MS, sans-serif",
        "Times New Roman, serif",
        "Courier New, monospace",
    ][profile["palette_seed"] % 8]

    layout_key = profile["body_kind"]
    template = LAYOUTS.get(layout_key, LAYOUTS["ledger"])

    values = {
        "page_bg": profile["page_bg"],
        "page_width": page_width,
        "page_height": page_height,
        "font_family": font_family,
      "table_class": "doc-table",
        "border_color": profile["border_color"],
        "header_color": profile["header_color"],
        "accent_color": profile["accent_color"],
        "table_bg": profile["table_bg"],
        "table_head_bg": profile["table_head_bg"],
        "table_alt_bg": profile["table_alt_bg"],
        "footer_bg": profile["footer_bg"],
        "layout_label": profile["layout_label"],
        "supplier_slug": supplier_slug(supplier_name),
    }

    return template.substitute(**values) + f"\n<!-- supplier: {html.escape(supplier_name)} | layout: {profile['layout_label']} | variant: {variant['key']} | digest: {digest[:10]} -->\n"


def load_suppliers() -> list[str]:
    if not SUPPLIERS_CSV.exists():
        raise FileNotFoundError(f"Missing supplier CSV: {SUPPLIERS_CSV}")

    with SUPPLIERS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        names = []
        for row in reader:
            name = (row.get("name") or "").strip().strip(",")
            if not name:
                continue
            names.append(name)
    return names


def main() -> None:
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    suppliers = load_suppliers()

    for name in suppliers:
        template_path = TEMPLATES_DIR / f"{supplier_slug(name)}.html"
        template_path.write_text(build_template(name), encoding="utf-8")

    print(f"Generated {len(suppliers)} supplier templates in {TEMPLATES_DIR}")


if __name__ == "__main__":
    main()
