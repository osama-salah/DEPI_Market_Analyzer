# AI Market Analyzer

The purpose of this project is to create an AI toolkit for market analysis. Its goal is to facilitate feasibility studies, competitor analysis, and pricing. 
The objective of this project is to create a market analysis tool that helps studying products in e-commerce websites, in addition to predicting the price and the demand of specific products.
The toolkit consists of three main components: Sentiment analyzer and ad generator,  price predictor, and demand predictor.
The sentiment analyzer tool scrapes e-commerce websites (such as Amazon), gets information about products, and fetches user comments. It then uses this information to  extract insights about the product. It uses the most reliable (upvoted) user reviews to compose a summary of the product, pros, and cons.
The ad generator uses the insights composed by the sentiment analyzer to write an ad for social media. It can generate an unlimited number of ads, from which the user can select the most appealing one. Specifying how the ad should sound could be determined at deployment. This includes: ad style, length, tone, emojis, links, …etc.
The price predictor tool uses price history data of a product to predict its price over a specific period of time or at a specific date. It supports rather complex change patterns and seasonality. The use cases of this tool include: feasibility studies, pricing/re-pricing products, and competitor analysis. The price history of a competing product could be obtained as explained in Appendix I. Currently, this tool uses only historical price data. A future work is to include other factors like aggregate social data (e.g. average income), stock market data, …etc.
The demand predictor tool uses order history data of a product to predict its demand over a specific period of time or at a specific date. It supports rather complex change patterns and seasonality. Currently, it uses only historical demand data. A future work is to include other factors like special offers, vacations, aggregate social data (e.g. average income), …etc.

## Installation
### Clone the repo

```
git clone https://github.com/depi-ml/DEPI_Market_Analyzer
```
### Create the ML server environment and install its requirements
```
cd DEPI_Market_Analyzer/ML_server
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch==2.4.1 --extra-index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
pip install -q -U google-generativeai
```
### Run the ML server
You should get a Gemini API key as explained here:
https://aistudio.google.com/app/apikey
```
GENAI_API_KEY="DUMMY_KEY" nohup python ml_server.py &
deactivate
```
### Install the price predictor requirements
```
cd ../price_predictor
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
## Configure the firewall for ML server
You should configure the firewall to allow inbound and outbound traffic on the used ports. The following configuration is just for guidance. You should customize your firewall depending on your specific needs.
### For Amazon Linux 2 (Redhat 7)
```
iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
iptables -A INPUT -p tcp --dport 5002 -j ACCEPT
```
### For Amazon Linux 2023 (Redhat 8+)
```
firewall-cmd --add-port=5000/tcp --permanent
firewall-cmd --add-port=5002/tcp --permanent
firewall-cmd --reload
```
### Run Price Predictor server
nohup python price_predictor.py &
deactivate

### Create the web server environment and install its requirements
```
cd ../web_server/
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install plotly
```
### Run the web servers
nohup python web_server.py &
nohup .venv/bin/streamlit run streamlit/home.py &

## Configure the firewall for the web servers
You should configure the firewall to allow inbound and outbound traffic on the used ports. The following configuration is just for guidance. You should customize your firewall depending on your specific needs.
### For Amazon Linux 2 (Redhat 7)
```
iptables -A INPUT -p tcp --dport 5001 -j ACCEPT
iptables -A INPUT -p tcp --dport 8501 -j ACCEPT
iptables -A OUTPUT -p tcp --sport 5001 -j ACCEPT
iptables -A OUTPUT -p tcp --sport 8501 -j ACCEPT
firewall-cmd --zone=public --add-port=5001/tcp --permanent
firewall-cmd --zone=public --add-port=8501/tcp --permanent
service firewalld restart
```
### For Amazon Linux 2023 (Redhat 8+)
```
firewall-cmd --add-port=5001/tcp --permanent
firewall-cmd --add-port=8501/tcp --permanent
firewall-cmd --reload
```




## License

[MIT](https://choosealicense.com/licenses/mit/)
