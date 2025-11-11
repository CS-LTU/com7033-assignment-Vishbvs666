from flask import Blueprint, render_template
from app.data.stroke_data import metrics, charts_bundle

bp = Blueprint("dashboard", __name__, url_prefix="/")

@bp.route("dashboard")
def dashboard_view():
    return render_template("dashboard/index.html", metrics=metrics(), charts=charts_bundle())
