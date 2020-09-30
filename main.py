def limit_spary_calculator_sans_q1(current_price, SL, p1, p2, risk, shape, norders):
    """
    shape: linear, parabolic
    risk: dollars
    p1: distance between final order and SL 
    p2: distance between first order and MKT
    """

    if current_price>SL:
        m=1
    else: m=-1

    del_p = (abs(current_price - SL)*(1-p2-p1))/(norders-1)

    prices = [current_price-p2*abs(current_price - SL)*m-sl*del_p*m for sl in range(norders)]

    if shape == 'parabolic':
        q_raw = [q**2 for q in range(1,norders+1)]
    else: 
        q_raw = list(range(1,norders+1))

    c = risk /(sum([q*p for q,p in zip(q_raw, prices)])-sum(q_raw)*SL)
    quantities = [c*q for q in q_raw]

    return prices, quantities

def limit_spary_calculator(current_price, SL, p1, p2, risk, shape, norders, q1=None):
    """
    shape: linear, parabolic
    risk: dollars
    p1: %distance between final order and SL 
    p2: %distance between first order and MKT
    q1: size of the first order (absolute)
    if norders ==1: q1 and p1 get ignored
    """

    if current_price>SL: # i.e. if long
        m=1
    else: m=-1

    if p2==1:
        return [SL], [0], SL, 0

    if norders==1:
        if p2==0:
            price = current_price
        else: 
            price = current_price-m*p2*abs(current_price - SL)
        quantity = -risk/(SL - price)
        return [price], [quantity], price, quantity

    if q1 is None or q1=='':
        prices, quantities = limit_spary_calculator_sans_q1(current_price, SL, p1, p2, risk, shape, norders)
        average_entry = sum([q*p for q,p in zip(quantities, prices)])/ sum(quantities)
        total_quantity = sum(quantities)
        return prices, quantities, average_entry, total_quantity


    if SL > current_price:
        q1=-abs(q1)
    else:
        q1=abs(q1)

    del_p = (abs(current_price - SL)*(1-p2-p1))/(norders-1)

    prices = [current_price-p2*abs(current_price - SL)*m-sl*del_p*m for sl in range(norders)]

    if shape == 'parabolic':
        q_raw = [q**2 for q in range(norders)]
    else: 
        q_raw = list(range(norders))

    if (sum([q*p for q,p in zip(q_raw, prices)])-sum(q_raw)*SL)==0:
        return [SL], [0], SL, 0

    c = (risk+SL*norders*q1-q1*sum([p for p in prices])) /(sum([q*p for q,p in zip(q_raw, prices)])-sum(q_raw)*SL)
    quantities = [c*q+q1 for q in q_raw]

    average_entry = sum([q*p for q,p in zip(quantities, prices)])/ sum(quantities)
    total_quantity = sum(quantities)

    return prices, quantities, average_entry, total_quantity


colors = {
    'TP-background':'#020100', 
    'TP-font':'#F1D302', 

    'SL-background':'#F1D302', 
    'SL-font':'#020100', 

    'long':'#228B22',
    'short':'#E83151',
    'accent':'#2B9EB3',

    'input-background':'#D9E9F2',

    'break':'#EEB902', 

    'risk':'#FF6F60',
    'rr':'#A78ACC',
    'reward':'#54B2E8',

    'risk_fee':'#FF220C',
    'rr_fee':'#8963BA',
    'reward_fee':'#1B98E0',    

    'tab_background': '#EBE9E9',
    'selected_tab_background': '#7A94A5',
    'disabled_tab_background' : '#EBE9E9'
    }



import plotly.graph_objects as go
def compute_and_plot(current_price,SL,p1,p2, risk, norders, shape, q1, **kwargs):
    if SL > current_price:
        color=colors['short']
    
    else:
        color=colors['long']

    prices, quantities, average_entry, total_quantity = limit_spary_calculator(current_price=current_price, SL=SL, p1=p1,p2=p2, q1=q1, risk=risk, shape=shape, norders=norders)
    sum([q*p for q,p in zip(quantities, prices)])-sum(quantities)*SL

    MKT_SL_len = -(max(quantities)+min(quantities))/2 *0.1
    fig = go.Figure([go.Bar(y=[current_price]+prices+[SL], x=[MKT_SL_len]+quantities+[MKT_SL_len], orientation='h',marker=dict(color = color))])

    # title = 'avg entry: {}, \n quantity:{}, \n cost: ${}, \n risk: ${}'.format(round(average_entry,2), round(total_quantity,2), round(total_quantity*average_entry,2),round(risk,2))

    # fig.update_layout(
    #     title=title,
    # )

    fig.update_layout(
        yaxis = dict(
            tickmode = 'array',
            tickvals = [current_price]+prices+[SL],
            ticktext = ['MKT: {}'.format(current_price)]+[round(p,4) for p in prices]+['SL: {}'.format(SL)]
        )
    )

    fig.update_layout(
        xaxis = dict(
            tickmode = 'array',
            tickvals = quantities,
            ticktext = [round(q,2) for q in quantities]
        )
    )
    return prices, quantities, average_entry, total_quantity, fig



import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_table.FormatTemplate as FormatTemplate
from dash_table.Format import Format, Scheme
import dash_core_components as dcc
import dash_html_components as html

from copy import deepcopy
import datetime

from flask import Flask


description_left = dcc.Markdown('''

    #### Inputs Glossary:

    **capital**: Capital

    **risk %**: Percentage of capital that would be lost should stoploss get triggered.

    **MKT**: Market price.

    **SL**: Stoploss price.

    **n. orders**: Number of (equally spaced) limit orders. 

    **init. q.**: (optional) Quantity of the first limit order. 

    **ΔSL**: Difference between market price and and last limit order expressed as a percentage of the difference between market price and stoploss price.

    **ΔMKT**: Difference between market price and and first limit order expressed as a percentage of the difference between market price and stoploss price.

    **TP**: Target price.

    **slippage**: (optional) Slippage.

    **mkr. fee**: (Optional) Percentage fee on limit orders. Positive implies fee paid, negative implies fee received.

    **tkr. fee**: (Optional) Percentage fee on market orders. Positive implies fee paid, negative implies fee received.

    **Quantity**: Ladder size increasing linearly vs. parabolically.

    **Risk slider**: Adjusts *risk %*.

    **ΔSL/ΔMKT slider:** The left slider adjusts ΔSL and the right slider adjusts ΔMKT.

    **N. ORDERS slider: ** Adjusts *n. orders*.


    ''')


description_right = dcc.Markdown('''

    #### Output Glossary:
    
    **avg. entry**: Average entry price if all limit orders are filled.

    **quantity**: Size of position if all limits are filled. <0 implies short, >0 implies long.

    **cost**: Total cost of position if all limits are filled.

    **eff. lev.**: Effective leverage if all limits are filled.

    **risk $**: Total sum lost if stoploss is triggered.

    **adj. risk $**: same as above but adjusted for fees and slippage.

    **reward $**: Total profit gained if all limits are filled and position is fully closed via limit order at target price.

    **adj. reward $**: Same as above but adjusted for fees (but not slippage since we assume exit via a limit order).

    **R:R **: Ratio of *reward $* to *risk $*.

    **adj. R:R**: Ratio of *adj. reward $* to *adj. risk $*.

    **plot**: x-axis is quantity, y-axis is price. 



    #### Caveats:

    ***Note***: if **n. orders** is set to 1, then **ΔSL** and **init. q.** are ignored



    ## [cyrusmaz.com](cyrusmaz.com)

    ''')



glossary = html.Div(
    children=[
        html.Div([description_left],style={'width':'40%','float':'left', 'margin-left': '5%'}),
        html.Div([description_right],style={'width':'40%','float':'left', 'margin-left': '5%'}),
        ], className="row", 
        )   


info = html.Div(
    children=[
        html.H1('Risk Management Abacus',style={'text-align':'center'}),
        glossary
        ],
    style={
    'width':'90%',
    'border': '2px solid black',
    'align':'center',
    'margin-left':'5%',
    'float':'left',
    'padding':'10px',
    'margin-bottom':'10px',
    'margin-top':'10px'}  
    )


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Flask(__name__)

dash_app = dash.Dash(
    name="some_name", 
    server=app, 
    title='Risk Abacus demo - cyrusmaz.com', 
    update_title=None,
    external_stylesheets=external_stylesheets)

price_precision = 2
money_precision = 2
quantity_precision = 2


button_style = {'margin':'5px','float':'left','display': 'inline', 'background-color':'white'}

tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': colors['tab_background'],
    'padding': '6px',
    'fontWeight': 'bold',
    'text-align': 'center',
    'font-family': 'HelveticaNeue',
    'font-size': '14px',
    'font-weight': '600',
    'height': '38px',
    'margin-bottom': '2px',
    'margin-top': '2px',
    'margin-left': '2px',
    'margin-right': '2px'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': colors['selected_tab_background'],
    'color': 'white',
    'padding': '6px',
    'fontWeight': 'bold',
    'text-align': 'center',
    'font-family': 'HelveticaNeue',
    'font-size': '16px',
    'font-weight': '600',
    'height': '38px',
    'margin-bottom': '2px',
    'margin-top': '2px',
    'margin-left': '2px',
    'margin-right': '2px'
}
    
input_table = dash_table.DataTable(
    id='input-table',
    columns=(
        [{'id': 'capital', 'name': 'capital','type':'numeric','format': FormatTemplate.money(money_precision)},
        {'id': 'risk_percent', 'name': 'risk %','type':'numeric','format': FormatTemplate.percentage(2)},
        {'id': 'current_price', 'name': 'MKT', 'type':'numeric','format': FormatTemplate.money(price_precision)},
        {'id': 'SL', 'name': 'SL','type':'numeric','format': FormatTemplate.money(price_precision)},
        {'id': 'norders', 'name': 'n. orders','type':'numeric'},
        {'id': 'q1', 'name': 'init. q.','type':'numeric'},
        {'id': 'p1', 'name': 'ΔSL','type':'numeric','format': FormatTemplate.percentage(1)},
        {'id': 'p2', 'name': 'ΔMKT','type':'numeric','format': FormatTemplate.percentage(1)},
        {'id': 'TP', 'name': 'TP','type':'numeric'},
        {'id': 'slippage', 'name': 'slippage','type':'numeric','format': FormatTemplate.money(price_precision)},
        {'id': 'maker_fee', 'name': 'mkr. fee','type':'numeric','format': FormatTemplate.percentage(2)},
        {'id': 'taker_fee', 'name': 'tkr. fee','type':'numeric','format': FormatTemplate.percentage(2)},
        ]
    ),
    style_header={
        'backgroundColor': 'grey',
        'color' : 'black',
        'text-align': 'center',
        'font-family': 'HelveticaNeue',
        'font-size': '14px',        
        'fontWeight': 'bold'
    },
    style_cell={ 
        'backgroundColor': '#CFCFCF',
        'font-family': 'HelveticaNeue',
        'font-size': '12px',        
        'fontWeight': 'bold'
    },
    style_data_conditional = [{'if': {'column_id': column},'backgroundColor': colors['accent']} for column in ['capital', 'SL', 'current_price','risk_percent']],
    style_data={
    'color': 'black',
    'whiteSpace': 'normal',
    'textAlign': 'center'
    # 'height': 'auto',
    # 'lineHeight': '15px'
    },    
    css=[
        {
        'selector': '.Select-menu-outer',
        'rule': '''--accent: black;'''
        },
        {
        'selector': '.Select-arrow',
        'rule': '''--accent: black;'''
        },              
        ],
        
    data=[{'capital':1000, 'current_price':4, 'SL':4.2, 'TP': 3, 'slippage':0, 'maker_fee':0, 'taker_fee':0.0007}],
    editable=True
)


output_summary_table = dash_table.DataTable(
    id='output-summary-table',
    columns=(
        [{'id': 'avg_entry', 'name': 'avg. entry', 'type':'numeric', 'format': FormatTemplate.money(price_precision)},
        {'id': 'quantity', 'name': 'quantity','type':'numeric', 'format':Format(precision=quantity_precision, scheme=Scheme.fixed)},
        {'id': 'cost', 'name': 'cost','type':'numeric', 'format': FormatTemplate.money(money_precision)},
        {'id': 'leverage', 'name': 'eff. lev.','type':'numeric', 'format':Format(precision=2, scheme=Scheme.fixed)},        
        
        {'id': 'risk', 'name': 'risk $','type':'numeric', 'format': FormatTemplate.money(money_precision)},
        {'id': 'risk_fee', 'name': 'adj. risk $','type':'numeric', 'format': FormatTemplate.money(money_precision)},   
        
        {'id': 'reward', 'name': 'reward $','type':'numeric', 'format': FormatTemplate.money(money_precision)},        
        {'id': 'reward_fee', 'name': 'adj. reward $','type':'numeric', 'format': FormatTemplate.money(money_precision)},                

        {'id': 'rr', 'name': 'R:R','type':'numeric', 'format':Format(precision=2, scheme=Scheme.fixed)},
        {'id': 'rr_fee', 'name': 'adj. R:R','type':'numeric', 'format':Format(precision=2, scheme=Scheme.fixed)},        
        # {'id': 'liq_price', 'name': 'liq. p.','type':'numeric', 'format': FormatTemplate.money(price_precision)},

        ]
    ),
    style_data_conditional = [
        {'if': {'column_id': 'risk_fee'},'backgroundColor': colors['risk_fee']},
        {'if': {'column_id': 'reward_fee'},'backgroundColor': colors['reward_fee']},
        {'if': {'column_id': 'rr_fee'},'backgroundColor': colors['rr_fee']},
        {'if': {'column_id': 'risk'},'backgroundColor': colors['risk']},
        {'if': {'column_id': 'reward'},'backgroundColor': colors['reward']},
        {'if': {'column_id': 'rr'},'backgroundColor': colors['rr']},        
        ],
    style_header={
        'backgroundColor': 'grey',
        'color' : 'black',
        'text-align': 'center',
        'font-family': 'HelveticaNeue',
        'font-size': '14px',        
        'fontWeight': 'bold'
    },
    style_cell={
        'backgroundColor': '#CFCFCF',
        'font-family': 'HelveticaNeue',
        'font-size': '12px',        
        'fontWeight': 'bold'
    },
    style_data={
    'color': 'black',
    'whiteSpace': 'normal',
    'textAlign': 'center'
    # 'height': 'auto',
    # 'lineHeight': '15px'
    },    
    
    editable=False
)

orders_table = dash_table.DataTable(
    id='orders-table',
    columns=(
        [{'id': 'price', 'name': 'price', 'type':'numeric', 'format': FormatTemplate.money(price_precision)},
        {'id': 'quantity', 'name': 'quantity','type':'numeric','format':Format(precision=quantity_precision, scheme=Scheme.fixed)},
        {'id': 'quantity_dollars', 'name': 'quantity $','type':'numeric', 'format': FormatTemplate.money(2)},
        {'id': 'type', 'name': 'type','type':'text'},
        ]
    ),

    export_format='csv',
    export_headers='display',
    merge_duplicate_headers=True,

    data=[],
    style_data_conditional=[
        {'if': {'filter_query': '{quantity} <0 && {type}=limit'},
        'backgroundColor': colors['short']},
        {'if': {'filter_query': '{quantity} >0 && {type}=limit'},
        'backgroundColor': colors['long']},        
        {'if': {'filter_query': '{quantity_dollars} <0 && {type}=limit'},
        'backgroundColor': colors['short']},
        {'if': {'filter_query': '{quantity_dollars} >0 && {type}=limit'},
        'backgroundColor': colors['long']},

        {'if': {'filter_query': '{type}=SL'},
        'backgroundColor': colors['SL-background'], 'color':colors['SL-font']},        
        
        {'if': {'filter_query': '{type}=TP'},
        'backgroundColor': colors['TP-background'], 'color':colors['TP-font']},                
    ],
    style_header={
        'backgroundColor': 'grey',
        'color' : 'black',
        'text-align': 'center',
        'font-family': 'HelveticaNeue',
        'font-size': '14px',        
        'fontWeight': 'bold'
    },
    style_cell={
        'backgroundColor': '#CFCFCF',
        'font-family': 'HelveticaNeue',
        'font-size': '12px',        
        'fontWeight': 'bold'
    },
    style_data={
    'color': 'black',
    'whiteSpace': 'normal',
    'textAlign': 'center'
    # 'height': 'auto',
    # 'lineHeight': '15px'
    },    
    editable=False
)


quantitiy_shape_radio = html.Div(dcc.RadioItems(
    id='shape-radio',
    options=[
        {'label': 'LINEAR', 'value': 'linear'},
        {'label': 'PARABOLIC', 'value': 'parabolic'},
    ],
    value='linear',
    labelStyle={'display': 'inline-block'}
))

limit_plot = dcc.Graph(
    id='limit-plot',config={'displayModeBar': False})

risk_slider = html.Div(dcc.Slider(
    id='risk-slider',
    min=0,
    max=20,
    step=0.005,
    value=1,
    marks={
        0: {'label': '0'},
        5: {'label': '5%'},
        10: {'label': '10%', 'style': {'color': '#f50'}},
        15: {'label': '15%', 'style': {'color': '#f50'}},
        20: {'label': '20%', 'style': {'color': '#f50'}}
    }))

p1_slider = html.Div(dcc.RangeSlider(
    id='p1-slider',
    min=0,
    max=1000,
    # step=0.0005,
    value=[200,950],
    pushable=0,
    marks={
        0: {'label': 'SL'},
        1000: {'label': 'MKT'}}
    ))

nodreders_slider = html.Div(dcc.Slider(
    id='norders-slider',
    min=1,
    max=100,
    step=1,
    value=10,
    marks={
        1: {'label': '1'},
        25: {'label': '25'},
        50: {'label': '50'},
        75: {'label': '75'},
        100: {'label': '100'}
    }))


norders_slider_html = html.Div(
    children=[
        html.Div(["N. ORDERS:", ],style={'width':'10%','float':'left'}),
        html.Div([nodreders_slider],style={'width':'80%','float':'left'}),
        ], className="row", style={'width':'90%','margin-left':'5%'})   

quantity_radio_html = html.Div(
    children=[
        html.Div(["QUANTITY:", ],style={'width':'11%','float':'left'}),
        html.Div([quantitiy_shape_radio],style={'width':'40%','float':'left'}),
        ], className="row", style={'width':'90%','margin-left':'5%','padding-top':'10px','padding-bottom':'10px'})   

risk_slider_html = html.Div(
    children=[
        html.Div(["RISK:", ],style={'width':'10%','float':'left'}),
        html.Div([risk_slider],style={'width':'80%','float':'left'}),
        ], className="row", style={'width':'90%','margin-left':'5%'})   

p1_slider_html = html.Div(
    children=[
        html.Div(["ΔSL/ΔMKT:", ],style={'width':'10%','float':'left'}),
        html.Div([p1_slider],style={'width':'80%','float':'left'}),
        ], className="row", style={'width':'90%','margin-left':'5%'})   

norders_slider_html = html.Div(
    children=[
        html.Div(["N. ORDERS:", ],style={'width':'10%','float':'left'}),
        html.Div([nodreders_slider],style={'width':'80%','float':'left'}),
        ], className="row", style={'width':'90%','margin-left':'5%'})   

risk_suite_left_side_html = html.Div([
    html.Div(
        children=[
            html.H5('INPUTS',style={'text-align':'center'}),
            input_table,
            quantity_radio_html,
            risk_slider_html,
            p1_slider_html,
            norders_slider_html,],
        style={
            # 'width':'90%',
            'border': '1px solid black',
            'align':'center',
            # 'margin-left':'5%',
            # 'float':'left',
            # 'background-color':colors['input-background'],
            'padding':'10px',
            'margin-bottom':'10px',
            'margin-top':'10px'} 
    ),
        
    output_summary_table,
    limit_plot,
    ])


output_radio = html.Div(dcc.RadioItems(
    id='output-radio',
    options=[
        {'label': '.csv', 'value': 'csv'},
        {'label': '.xlsx', 'value': 'xlsx'},
    ],
    value='csv',
    labelStyle={'display': 'inline-block'}
))


risk_suite_right_side_html = html.Div(
    children=[
        output_radio,
        orders_table,
        ])

risk_suite_html = html.Div(
    children=[
        html.Div([risk_suite_left_side_html],style={'width':'80%','float':'left'}),
        html.Div([risk_suite_right_side_html],style={'width':'18%','float':'left','margin-left':'2%'}),
        ], className="row",    
        style={
            'width':'90%',
            'border': '2px solid black',
            'align':'center',
            'margin-left':'5%',
            'float':'left',
            'padding':'10px',
            'margin-bottom':'10px',
            'margin-top':'10px'}) 

####################################################



dash_app.layout=html.Div([info, risk_suite_html])


### SLIDERS AND SET PRICE
@dash_app.callback(
    Output(component_id='input-table' ,component_property='data'),
    [Input(component_id='risk-slider' ,component_property='value'),
    Input(component_id='p1-slider' ,component_property='value'),
    Input(component_id='norders-slider' ,component_property='value'),],
    [State(component_id='input-table' ,component_property='data'),])
def update_input_tables(
    value, 
    p1_slide, 
    norders_slide, 
    data, 
    ):

    data[0]['risk_percent']=value/100
    data[0]['norders']=norders_slide
    if 'current_price' in data[0].keys() and 'SL' in data[0].keys():
        SL =  data[0]['SL']
        current_price = data[0]['current_price']

        data[0]['p1']=min(p1_slide)/1000
        data[0]['p2']=1-max(p1_slide)/1000
    return data


## LIMIT PLOT AND ORDER SUMMARY TABLE
@dash_app.callback(
    [Output(component_id='limit-plot' ,component_property='figure'),
    Output(component_id='output-summary-table' ,component_property='data'),
    Output('orders-table','data')],
    [Input(component_id='input-table' ,component_property='data'),
    Input(component_id='shape-radio' ,component_property='value'),])
def update_custom_schedule_plot(data, shape):
    print(shape)
    empty_fig = go.Figure()
    datum=data[0].copy()
    if sum([k in {'capital', 'current_price', 'SL', 'p1', 'risk_percent', 'norders'} and datum[k]!='' for k in datum.keys()])<6:
        return empty_fig, [{}], []
    datum['shape']=shape
    print('risk_percent: {}'.format(datum['risk_percent']))
    datum['risk']=datum['risk_percent']*datum['capital']
    print(datum)
    if 'q1' not in datum.keys():
        datum['q1']=None
    prices, quantities, average_entry, total_quantity, fig = compute_and_plot(**datum)
    # fig.update_layout(height=600) ## INCREASE HEIGHT
    fig.update_layout(xaxis_fixedrange=True, yaxis_fixedrange=True,) ## DISABLE ZOOMING!
    TP = None
    if 'TP' in datum.keys() and datum['TP'] is not None and datum['TP'] != '':
        TP = datum["TP"]
        reward = (datum["TP"] - average_entry)*total_quantity
    else:
        reward = -1
    
    if reward ==-1:
        RR = -1
    else: 
        RR = reward/datum['risk']

    ###FEE AND SLIPPAGE COMPUTATIONS

    ## FIX MAKER FEE
    if 'maker_fee' not in datum.keys() or datum['maker_fee']=='' or datum['maker_fee'] is None:
        maker_fee = 0
    else:
        maker_fee = datum['maker_fee']

    ## FIX TAKER FEE
    if 'taker_fee' not in datum.keys() or datum['taker_fee']=='' or datum['taker_fee'] is None:
        taker_fee = 0
    else:
        taker_fee = datum['taker_fee']        

    ## FIX SLIPPAGE
    if 'slippage' not in datum.keys() or datum['slippage']=='' or datum['slippage'] is None:
        slippage = 0
    else:
        slippage = datum['slippage'] 

    ## FIX SL
    SL = datum['SL'] 
    current_price = datum['current_price']

    limit_fees = sum([p*abs(q)*maker_fee for p,q in zip(prices,quantities)])

    if current_price>SL:
        m=1
    else: m=-1    

    # print('slippage: {}'.format(slippage))
    SL_fees = (datum['SL'] -m*slippage)*abs(total_quantity)*taker_fee

    if TP is not None:
        TP_fees = TP*abs(total_quantity)*maker_fee
    else: 
        TP_fees = 0

    risk_slippage = slippage*abs(total_quantity)

    risk_fee = datum['risk'] + SL_fees + limit_fees + risk_slippage

    reward_fee = reward - limit_fees - TP_fees

    if risk_fee !=0:
        rr_fee = reward_fee / risk_fee
    else:
        rr_fee = None

    leverage = abs(total_quantity)*average_entry/datum['capital']

    table_output = dict(
        avg_entry = average_entry,
        quantity = total_quantity,
        cost = average_entry*abs(total_quantity),
        risk = datum['risk'],
        risk_fee = risk_fee,
        reward_fee = reward_fee,
        rr_fee = rr_fee,
        reward = reward,
        rr= RR,
        leverage = leverage)
    
    orders_table = [{'price':p, 'quantity':q, 'type':'limit', 'quantity_dollars':p*q} for p,q in zip(prices, quantities)]
    if datum['SL']>datum['current_price']:
        orders_table.insert(0, {'price':datum['SL'], 'quantity':-total_quantity, 'type':'SL', 'quantity_dollars':datum['SL']*-total_quantity} )
        if 'TP' in datum.keys() and datum['TP'] is not None and datum['TP'] != '':
            if datum['TP']<datum['current_price']:
                orders_table.append({'price':datum['TP'], 'quantity':-total_quantity, 'type':'TP', 'quantity_dollars':datum['TP']*-total_quantity} )

    else:
        orders_table.append({'price':datum['SL'], 'quantity':-total_quantity, 'type':'SL', 'quantity_dollars':datum['SL']*-total_quantity} )
        if 'TP' in datum.keys() and datum['TP'] is not None and datum['TP'] != '':
            if datum['TP']>datum['current_price']:            
                orders_table.insert(0, {'price':datum['TP'], 'quantity':-total_quantity, 'type':'TP', 'quantity_dollars':datum['TP']*-total_quantity} )

    return fig, [table_output], orders_table


@dash_app.callback(
    Output('orders-table', 'export_format'),
    Input('output-radio','value'))
def output_radio(value):
    print(value)
    if value == 'xlsx':
        return 'xlsx'
    else:
        return 'csv'





if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug = True)
