import os
import json
from flask import Flask, request, jsonify
import flask_excel as excel
from sqlalchemy.dialects.mysql import TIME
from flask import Flask,render_template, request, g
from flask import Flask, request, flash, url_for, redirect, \
     render_template, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from sqlalchemy.sql import func
from flask_cors import CORS, cross_origin
from act_group import act_grp
import calendar
from dateutil.relativedelta import relativedelta

#from apscheduler.scheduler import Scheduler
#import atexit
def left(s, amount):
    return s[:amount]

def right(s, amount):
    return s[-amount:]

def mid(s, offset, amount):
    return s[offset:offset+amount]

def convert_to_julian(period):
    x = str(period)
    i_year = int(left(x,4))
    if int(right(x,2))<=2:
        i_year = i_year-1 
    
    i_month = fiscal_choose[int(right(x,2))]
    cal = datetime(i_year,i_month,1)

    result = (calendar.month_abbr[cal.month]+"-"+right(str(cal.year),2))
    return result


app = Flask(__name__)
app.config.from_pyfile(os.path.abspath('pod_db.cfg'))
global db
db = SQLAlchemy(app)
migrate = Migrate(app,db)
#cors = CORS(app)
excel.init_excel(app)

global fiscal_choose

fiscal_choose = {1:11,2:12,3:1,4:2,5:3,6:4,7:5,8:6,9:7,10:8,11:9,12:10,13:10}

class trans(db.Model):
    __tablename__ = "trans_BW"
    id = db.Column('trans_id', db.Integer, primary_key=True)
    vend_id = db.Column(db.Integer)
    #read_time = db.Column(db.DateTime)
    vend_text = db.Column(db.String)
    trans_text = db.Column(db.String)
    resno = db.Column(db.Integer)
    resno_text = db.Column(db.String)
    order_num = db.Column(db.Integer)
    trans_num = db.Column(db.Integer)
    trans_date = db.Column(db.DateTime)
    cost_type = db.Column(db.String)
    gl = db.Column(db.Integer)
    gl_text = db.Column(db.String)
    act_group = db.Column(db.String)
    act_int = db.Column(db.Integer)
    act_code = db.Column(db.String)
    act_text = db.Column(db.String)
    period = db.Column(db.Integer)
    cal_period = db.Column(db.String)
    amount = db.Column(db.Float)


    def __init__(self, vend_id,vend_text,trans_text, resno, resno_text, order_num, trans_num, trans_date, cost_type,
        gl, gl_text, act_group, act_code, act_text, period, trans_amount):

        self.vend_id = vend_id
        self.vend_text = vend_text
        self.trans_text = trans_text
        self.resno = resno
        self.resno_text = resno_text
        self.order_num = order_num
        self.trans_num = trans_num
        self.trans_date = trans_date
        self.cost_type = cost_type
        self.gl = gl
        self.gl_text = gl_text
        self.act_group = act_group
        self.act_int = act_grp[act_group]
        self.act_code = act_code
        self.act_text = act_text
        self.period = period
        self.amount = trans_amount
        self.cal_period = convert_to_julian(period)

@app.route("/summary", methods=['GET'])
#@cross_origin()
def summary():

    end_sum = db.session.query(trans.act_group.label("act_group"),func.sum(trans.amount).label('total')).group_by(trans.act_group).order_by(trans.act_int)
    result = convert_q_json(end_sum)
    
    final_totals = {}
    final_totals['bounds'] = bounds
    #final_totals['totals'] = result

    response = app.response_class(
        response=json.dumps(final_totals),
        status=200,
        mimetype='application/json'
    )
    print(response)
    return response

def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

@app.route("/bounds", methods=['GET'])
def make_bounds():
    bounds = {}
    bounds['min']=(db.session.query(func.min(trans.period)).scalar())
    bounds['max']=(db.session.query(func.max(trans.period)).scalar())
    cal_bounds = {}
    for i in bounds:
        x = str(bounds[i])
        i_year = int(left(x,4))
        if int(right(x,2))<=2:
            i_year = i_year-1 
        
        i_month = fiscal_choose[int(right(x,2))]
        cal_bounds[i] = datetime(i_year,i_month,1)
    month_count = (diff_month(cal_bounds['max'],cal_bounds['min'])) + 1

    result = []
    for x in range(month_count):
        make_this = (cal_bounds['min']+relativedelta(months=+x))
        result.append(calendar.month_abbr[make_this.month]+"-"+right(str(make_this.year),2))
    return result




@app.route("/summary_period", methods=['GET'])
def summary_w_period():
    if request.is_xhr:
        end_sum = db.session.query(trans.id.label("id"),trans.act_group.label("act_group"),func.sum(trans.amount).label('total')).group_by(trans.act_group).order_by(trans.act_int)
        totals = convert_q_json(end_sum)
        periods = get_distinct()
        iter_x = 0
        for x in totals: #iter over TOTALS
            current = (x["act_group"])

            for y in periods[iter_x]: #iter over periods
                totals[iter_x][y['cal_period']] = y['total']
            iter_x +=1
        # final_totals = {}
        # final_totals['bounds'] = make_bounds()
        # final_totals['totals'] = totals
        print(json.dumps(totals))
        response = app.response_class(
            response=json.dumps(totals),
            status=200,
            mimetype='application/json'
        )
        print(response)
        return response
    else:
        return render_template('periods.html')

@app.route('/')
def main_report():


    print(bounds)
    return render_template('tab-ajax.html')


@app.route('/js_sand')
def js_sand():
    print(bounds)
    return render_template('js-sand.html')

@app.route("/distinct", methods=['GET'])
def get_distinct():
    lookie = db.session.query(trans.act_group).distinct(trans.act_group).order_by(trans.act_int).all()

    period_summary = []
    for x in lookie:
        print(x[0])
        end_sum = db.session.query(trans.act_group.label("act_group"),func.sum(trans.amount).label('total'), trans.cal_period.label('cal_period')).filter(trans.act_group==str(x[0])).group_by(trans.period).order_by(trans.act_int)
        new_period = convert_q_json(end_sum)
        period_summary.append(new_period)
    return period_summary
    #return jsonify({"result": "success"})


@app.route("/upload", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        db.session.query(trans).delete()
        db.session.commit()
        x = request.get_array(field_name='file')
        just_data = []
        iter_x = iter(x)
        y = 0
        for y in range(6):
            next(iter_x)
        for trans_row in iter_x:
            if len(trans_row[3]) == 0 or trans_row[3] == ' ':
                continue
            else:
                just_data.append(trans_row)

        end_sum = 0
        for look in just_data:
            new_trans = trans(look[1],look[2],look[3],look[4],look[5],look[6],look[8],look[9],look[10],look[11],look[12],look[13],look[14],look[15],look[16],look[17])
            db.session.add(new_trans)
            db.session.commit()
            end_sum += float(look[17])


        return jsonify({"result": "success"})

    return '''
    <!doctype html>
    <title>Upload an excel file</title>
    <h1>Excel file upload (csv, tsv, csvz, tsvz only)</h1>
    <form action="" method=post enctype=multipart/form-data><p>
    <input type=file name=file><input type=submit value=Upload>
    </form>
    '''


def convert_q_json(mixup):
    field_names = []
    for x in mixup.column_descriptions:
        field_names.append(x["name"])
    new_sum = mixup.all()
    result = []
    for x in new_sum:
        dict_ent = {}
        iterate = 0
        for y in field_names:
            dict_ent[y] = x[iterate]
            iterate += 1
        result.append(dict_ent)
    return (result)

def convert_q_json_period(mixup):
    field_names = []
    for x in mixup.column_descriptions:
        field_names.append(x["name"])
    new_sum = mixup.all()
    result = []
    for x in new_sum:
        dict_ent = {}
        iterate = 0
        for y in field_names:
            dict_ent[y] = x[iterate]
            iterate += 1
        result.append(dict_ent)
    return (result)

def start_over():
    db.reflect()
    db.drop_all()

if __name__ == "__main__":
    #start_over()
    db.create_all()
    app.run(use_reloader=True,debug=True)