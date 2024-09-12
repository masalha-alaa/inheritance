from flask import Flask, request, jsonify, render_template
from heirs import Heirs
from fiqh import Fiqh
from inheritance import get_results
from pprint import pprint
from my_utils import HeirsOrderInHtml as HOIH

# DEBUG = True
DEBUG = False


# TODO: Find in another project if this solves the multi app instances
app = Flask(__name__)
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
    _, _, _, result = get_results(problem, estate)  # Modify this line according to your class method

    if DEBUG:
        print("Ali Aloush:")
        pprint(result, sort_dicts=False)

    # Return the results as JSON
    return jsonify({'study': list(result.values())})


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
    result = app.fiqh.run(problem)  # Modify this line according to your class method

    if DEBUG:
        print("Fiqh:")
        pprint(result, sort_dicts=False)

    # Return the results as JSON
    return jsonify({'fiqh': list(result.values())})
    # return jsonify({'study': [[', '.join([str(x) for x in r])] for r in result.values()], 'fiqh': [0] * 9})


if __name__ == '__main__':
    app.run(debug=True)
