class TextStorage():
    title:str
    index_choice_label:str
    slider_label:str
    chart_y_axis:str
    chart_x_axis:str
    instructions:str
    strategy_choice_label:str
    strategy_1_name:str 
    strategy_2_name:str
    strategy_1_description:str
    strategy_2_description:str
    down_percent_description:str
    max_months_description:str
    max_months_default:str
    investment_horizon:str
    investment_horizon_help:str
    cost_average:str
    cost_average_help:str
    dont_use:str
    years:str
    months:str
    average_return_text:str
    confidence_interval_part_1:str
    confidence_interval_part_2:str
    average_days_text:str
    not_invested_share_text:str
    run_button_text:str
    strategy_results:str
    all_results:str
    clear_button:str
           
class EnglishTextStorage(TextStorage):
    def __init__(self) -> None:
        super().__init__()
        
        self.title = 'Can you time the market?'
        self.index_choice_label = 'Index used'
        self.slider_label = 'Date range to consider for the analysis:'
        self.chart_y_axis = 'Index Level (normalized)'
        self.chart_x_axis = 'Year'
        self.instructions = '''Below you can set up a simple investment strategy and test how well it would 
            have performed in the past.  \n For now, you have the possibility to wait for the market to first 
            fall for x-% before you invest. Optionally, you can also specify a maximum time before you end up 
            investing anyways (even if the market did not fall enough according to your input).  \n Additional 
            settings allow for choosing the investment duration (investment horizon) and to spread the investment
            across a defined timeframe using multiple partial investments (Cost Average Investing).'''
        self.strategy_choice_label = 'Choose investment strategy:'
        self.strategy_1_name = 'Market down x-%'
        self.strategy_2_name = 'Market down x-% (inc. max waiting time)'
        self.strategy_1_description = 'Wait until the market goes down x-%'
        self.strategy_2_description = """Wait until the market goes down x-% (if it hasn't gone down after n-months, 
            invest anyway)"""
        self.down_percent_description = 'How much should the market fall compared to the initial index level before you invest (in %)?'
        self.max_months_description = 'How many months do you want to wait at most before investing?'
        self.max_months_default = 'no limit'
        self.investment_horizon = 'Investment horizon'
        self.investment_horizon_help = 'How many years do you want to invest? ("max" = for each investment date, the maximum duration until the last date available is considered)'
        self.cost_average = 'Spread across n months (Cost Average Investing)'
        self.cost_average_help = 'The investment is split into n parts, where 1/n of the total is invested every month (for the next n months)'
        self.dont_use = 'do not use'
        self.years = 'year(s)'
        self.months = 'month(s)'
        self.average_return_text = 'Average return (per year) of your strategy: '
        self.confidence_interval_part_1 = ' [95% of returns between '
        self.confidence_interval_part_2 = ' and '
        self.average_days_text = 'Average number of days waited before investing: '
        self.not_invested_share_text = 'Share of cases that did not invest within set period: '
        self.run_button_text = 'Run strategy'
        self.strategy_results = 'Current strategy results:'
        self.all_results = 'All results'
        self.clear_button = 'Clear table'
        
class GermanTextStorage(TextStorage):
    def __init__(self) -> None:
        super().__init__()
        
        self.title = 'Kannst du den Markt timen?'
        self.index_choice_label = 'Ausgewählter Index'
        self.slider_label = 'Betrachtungszeitraum der Analyse:'
        self.chart_y_axis = 'Index Level (normalisiert)'
        self.chart_x_axis = 'Jahr'
        self.instructions = '''Im Folgenden ist es möglich, eine einfache Anlagestrategie aufzustellen und zu testen, 
        wie gut diese in der Vergangenheit performt hätte.  \n Aktuell gibt es die Möglichkeit, die Investition 
        zurückzuhalten, bis der Markt um x-% gefallen ist. Optional lässt sich zusätzlich eine maximale 
        Zeitspanne angeben, bevor trotzdem investiert werden soll (auch wenn der Markt der Eingabe entsprechend 
        noch nicht genug gefallen ist).  \n Weitere Einstellungen ermöglichen das Festlegen der Dauer des Investments 
        sowie die Möglichkeit das Investment mit mehreren Teilinvestments über einen definierten Zeitraum zu strecken.'''
        self.strategy_choice_label = 'Wähle eine Investment Strategie:'
        self.strategy_1_name = 'Markt um x-% gefallen'
        self.strategy_2_name = 'Markt um x-% gefallen (inkl. maximale Wartezeit)'
        self.strategy_1_description = 'Warten bis der Markt um x-% gefallen ist'
        self.strategy_2_description = """Warten bis der Markt um x-% gefallen ist (nach n-Monaten trotzdem investieren, 
        auch wenn der Markt noch keine x-% gefallen ist)"""
        self.down_percent_description = 'Wie viel % soll der Markt im Vergleich zum Startwert gefallen sein, damit investiert wird?'
        self.max_months_description = 'Wie viele Monate soll maximal gewartet werden, bevor investiert wird?'
        self.max_months_default = 'kein Limit'
        self.investment_horizon = 'Dauer des Investments'
        self.investment_horizon_help = 'Anzahl der Jahre für die investiert wird ("max" = für jedes Einstiegsdatum wird der maximale Zeitraum bis zum letzten verfügbaren Datum betrachtet)'
        self.cost_average = 'Investment auf n Monate verteilen (Cost Average Investing)'
        self.cost_average_help = 'Das initiale Investment wird in n Teile unterteilt, von denen jeweils ein Teil pro Monat investiert wird (für die folgenden n Monate)'
        self.dont_use = 'Nicht nutzen'
        self.years = 'Jahr(e)'
        self.months = 'Monat(e)'
        self.average_return_text = 'Durchschnittliche Rendite (pro Jahr) der Strategie: '
        self.confidence_interval_part_1 = ' [95% der Renditen zwischen '
        self.confidence_interval_part_2 = ' und '
        self.average_days_text = 'Durchschnittliche Wartezeit (in Tagen) bevor investiert wurde: '
        self.not_invested_share_text = 'Anteil der Fälle, in denen innerhalb des festgelegten Zeitraums nicht investiert wurde: '
        self.run_button_text = 'Strategie testen'
        self.strategy_results = 'Ergebnis der aktuellen Strategie:'
        self.all_results = 'Alle Ergebnisse'
        self.clear_button = 'Tabelle zurücksetzen'
       