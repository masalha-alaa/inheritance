from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from heirs import Heirs
from fiqh import Fiqh
from inheritance import get_results
from pprint import pprint
from my_utils import HeirsOrderInHtml as HOIH


app = Flask(__name__)
app.config['DEBUG'] = False
# app.config['DEBUG'] = True
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # Limit to 8MB
CORS(app)
app.fiqh = Fiqh()
app.fiqh.initialize()


# Define a route to serve the HTML file
@app.route('/')
def index():
    return render_template('index.html')  # Ensure 'index.html' is in a 'templates' folder


# Define a route to handle the data and run the algorithm
@app.route('/calculate_heritage', methods=['POST'])
def calculate_heritage():
    data = request.json  # Receive the data sent from the front-end
    heirs = data.get('heirs')  # Extract the 'heirs' array (the "Number" column)
    estate = int(data.get('estate', 24))  # Get estate value
    problem = Heirs(husband=heirs[HOIH.HUSBAND.value],
                    wife=heirs[HOIH.WIFE.value],
                    son=heirs[HOIH.SON.value],
                    daughter=heirs[HOIH.DAUGHTER.value],
                    father=heirs[HOIH.FATHER.value],
                    mother=heirs[HOIH.MOTHER.value],
                    brother=heirs[HOIH.BROTHER.value],
                    sister=heirs[HOIH.SISTER.value],
                    relatives=heirs[HOIH.RELATIVES.value])

    # Run the algorithm and get the results
    the_case, _, _, result = get_results(problem, estate)  # Modify this line according to your class method

    if app.config['DEBUG'] is True:
        print("Ali Aloush:")
        pprint(result, sort_dicts=False)
        print(the_case)

    # Return the results as JSON
    return jsonify({'study': list(result.values()), 'error': len(result) == 0, 'case': the_case.name,
                    'awl': False})


# Define a route to handle the data and run the algorithm
@app.route('/calculate_heritage_fiqh', methods=['POST'])
def calculate_heritage_fiqh():
    data = request.json  # Receive the data sent from the front-end
    heirs = data.get('heirs')  # Extract the 'heirs' array (the "Number" column)
    problem = Heirs(husband=heirs[HOIH.HUSBAND.value],
                    wife=heirs[HOIH.WIFE.value],
                    son=heirs[HOIH.SON.value],
                    daughter=heirs[HOIH.DAUGHTER.value],
                    father=heirs[HOIH.FATHER.value],
                    mother=heirs[HOIH.MOTHER.value],
                    brother=heirs[HOIH.BROTHER.value],
                    sister=heirs[HOIH.SISTER.value],
                    relatives=heirs[HOIH.RELATIVES.value])

    # Run the algorithm and get the results
    result, awl_applied = app.fiqh.run(problem)  # Modify this line according to your class method

    if app.config['DEBUG'] is True:
        print("Fiqh:")
        pprint(result, sort_dicts=False)
        print(f"{awl_applied = }")

    # Return the results as JSON
    return jsonify({'fiqh': list(result.values()), 'error': len(result) == 0, 'case': None, 'awl': awl_applied})
    # return jsonify({'study': [[', '.join([str(x) for x in r])] for r in result.values()], 'fiqh': [0] * 9})


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
