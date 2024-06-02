# Импортируем необходимые модули и классы из Flask, Flask-WTF и SQLAlchemy.
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask_restful import Api, Resource

# Создаем экземпляр Flask приложения.
app = Flask(__name__)

# Настраиваем URI для подключения к базе данных SQLite.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reports.db'

# Настраиваем секретный ключ для защиты данных формы.
app.config['SECRET_KEY'] = 'your_secret_key'

# Создаем экземпляр SQLAlchemy для управления базой данных.
db = SQLAlchemy(app)

api = Api(app)

# Определяем модель базы данных для хранения отчетов. Каждый отчет имеет идентификатор (id), полное имя (full_name) и текст отчета (report_text).
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    report_text = db.Column(db.Text, nullable=False)

# Определяем форму для отправки отчетов с полями для полного имени и текста отчета. Все поля формы являются обязательными для заполнения.
class ReportForm(FlaskForm):
    full_name = StringField('ФИО', validators=[DataRequired()])
    report_text = TextAreaField('Отчёт', validators=[DataRequired()])
    submit = SubmitField('Отправить')

# Определяем маршрут для главной страницы приложения, которая отображает форму для отправки отчета.
@app.route('/', methods=['GET', 'POST'])
def index():
    form = ReportForm()
    # Если форма отправлена и валидна, создаем новый отчет и сохраняем его в базе данных.
    if form.validate_on_submit():
        full_name = form.full_name.data
        report_text = form.report_text.data
        new_report = Report(full_name=full_name, report_text=report_text)
        db.session.add(new_report)
        db.session.commit()
        return render_template('success.html')
    # Если данные формы некорректны или форма не была отправлена, отображаем форму.
    return render_template('index.html', form=form)

# Определяем маршрут для получения отчетов по заданному критерию (all или by_name).
@app.route('/reports/<criteria>', methods=['GET'])
def get_reports(criteria):
    # Если критерий равен all, получаем все отчеты и отображаем их.
    if criteria == 'all':
        reports = Report.query.all()
        return render_template('all_reports.html', reports=reports)
    else:
        # Если критерий равен by_name, получаем имя из параметров запроса, фильтруем отчеты по этому имени и отображаем их.
        # Пример: /reports/by_name?name=artem
        if criteria == 'by_name':
            name = request.args.get('name')
            reports = Report.query.filter_by(full_name=name).all()
            return render_template('reports_by_name.html', reports=reports, name=name)
        # Если критерий некорректен, возвращаем JSON с ошибкой.
        else:
            return jsonify({'error': 'Invalid criteria'}), 400
    # Возвращаем JSON с отчетами, если никакой критерий не указан.
    result = [{'full_name': report.full_name, 'report_text': report.report_text} for report in reports]
    return jsonify(result)

# Создаем класс ReportAPI, который наследуется от Resource и будет обрабатывать запросы к API.
class ReportAPI(Resource):
    # Метод get обрабатывает GET-запросы.
    def get(self, report_id=None):
        #  Если передан report_id, он возвращает отчет с этим ID.
        if report_id:
            # Пытается найти отчет по ID, возвращает 404 ошибку, если отчет не найден.
            report = Report.query.get_or_404(report_id)
            return {'id': report.id, 'full_name': report.full_name, 'report_text': report.report_text}
        # Если report_id не передан, возвращает все отчеты.
        else:
            reports = Report.query.all()
            return [{'id': report.id, 'full_name': report.full_name, 'report_text': report.report_text} for report in reports]
    # Метод post обрабатывает POST-запросы для создания нового отчета.
    def post(self):
        data = request.get_json()   # Получает данные запроса в формате JSON.
        new_report = Report(full_name=data['full_name'], report_text=data['report_text'])   # Создается новый объект Report с данными из запроса.
        db.session.add(new_report)  # Новый отчет в сессию базы данных и коммитим изменения.
        db.session.commit()
        return {'id': new_report.id, 'full_name': new_report.full_name, 'report_text': new_report.report_text}, 201 # Возвращает созданный отчет с HTTP статусом 201 (Created).
    # Метод delete обрабатывает DELETE-запросы для удаления отчета по ID.
    def delete(self, report_id):
        report = Report.query.get_or_404(report_id)
        db.session.delete(report)   # Удаляет найденный отчет из сессии базы данных и коммитит изменения.
        db.session.commit()
        return '', 204  # Возвращает пустой ответ с HTTP статусом 204.

# Здесь мы регистрируем ресурс ReportAPI и задаем пути /api/reports и /api/reports/<int:report_id>, по которым будут обрабатываться запросы.
api.add_resource(ReportAPI, '/api/reports', '/api/reports/<int:report_id>')

# Если этот файл выполняется как основной, создаем все таблицы базы данных (если они еще не существуют) и запускаем Flask приложение в режиме отладки.
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)



    # 23.106.56.53