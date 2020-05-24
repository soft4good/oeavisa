```bash
pip3 install virtualenv
virtualenv .
source bin/activate
pip3 install -r requirements.txt
cd bots
cp oeavisa/.env.sample oeavisa/.env
# update .env with correct values !!!
scrapy crawl cuba
```