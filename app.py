from flask import Flask, render_template, request, jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo

#create a flask app
app = Flask(__name__)

#create a route to access the function
#Base URL
@app.route('/', methods = ['GET'])
#cross_origin-It requires only for cloud deployment and not for local deployment
@cross_origin()
def homepage():
    return render_template("index.html")

#This route is responsible to show the reviews of the product
@app.route('/review',methods=['POST','GET'])
@cross_origin()
def index():
    # if it is a POST request then we can execute further
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ", "")
        try:
            #Opening a connection in mongo
            dbConn =pymongo.MongoClient("mongodb://localhost:27017/")
            #Connect to the database called 'Review_Scrapper
            db =dbConn['Review_Scrapper']
            #searching the collection with the name same as the keyword
            reviews = db[searchString].find({})
            if reviews.count()>0: #if there is a collection with searched keyword and it has records in it
                return render_template('results.html',reviews=reviews)
            else:

                flipkart_url = "https://www.flipkart.com/search?q=" + searchString

                uClient = uReq(flipkart_url)

                flipkartPage = uClient.read()

                uClient.close()

                flipkart_html = bs(flipkartPage, "html.parser")

                bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})

                del bigboxes[0:3]

                box = bigboxes[0]
                productLink = "https://www.flipkart.com" + box.div.div.div.a['href']

                prodRes = requests.get(productLink)
                prodRes.encoding = 'utf-8'

                prod_html = bs(prodRes.text, "html.parser")
                print(prod_html)

                commentboxes = prod_html.find_all('div', {'class': "_16PBlm"})

                # creating a collection with the same name as search string. Tables and Collections are analogous.
                table =db[searchString]

                #filename = searchString + ".csv"
                #fw = open(filename, "w")
                #headers = "Product, Customer Name, Rating, Heading, Comment \n"
                #fw.write(headers)
                reviews = []
                for commentbox in commentboxes:
                    try:
                        # name.encode(encoding='utf-8')
                        name = commentbox.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text

                    except:
                        name = 'No Name'

                    try:
                        # rating.encode(encoding='utf-8')
                        rating = commentbox.div.div.div.div.text


                    except:
                        rating = 'No Rating'

                    try:
                        # commentHead.encode(encoding='utf-8')
                        commentHead = commentbox.div.div.div.p.text

                    except:
                        commentHead = 'No Comment Heading'
                    try:
                        comtag = commentbox.div.div.find_all('div', {'class': ''})
                        # custComment.encode(encoding='utf-8')
                        custComment = comtag[0].div.text
                    except Exception as e:
                        print("Exception while creating dictionary: ", e)

                    mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                          "Comment": custComment}
                    #insert the dictionary values to collection in mongo db
                    x = table.insert_one(mydict)
                    reviews.append(mydict)
                return render_template('results.html', reviews=reviews[0:(len(reviews) - 1)])
        except Exception as e:
            print('The Exception message is: ', e)
            return 'something is wrong'
    # return render_template('results.html')

        else:
            return render_template('index.html')


if __name__ == "__main__":
    # app.run(host='127.0.0.1', port=8001, debug=True)
    app.run(debug=True)


