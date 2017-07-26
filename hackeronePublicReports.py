import requests, json
from multiprocessing.dummy import Pool as ThreadPool 
from pymongo import MongoClient

requests.packages.urllib3.disable_warnings()

# mongodb config
MONGO_HOST = '127.0.0.1'
MONGO_PORT = 27017
MONGO_USERNAME = ''
MONGO_PASSWORD = ''

client = MongoClient(MONGO_HOST,MONGO_PORT)
db=client.hackerone_reports			# db initialization

dictbugs = {}

POOL_SIZE = 20
Base_url = 'https://hackerone.com'
Out_file = 'old_reports.csv'
READ_MODE = 'r'
WRITE_MODE = 'w'
APPEND_MODE = 'a'

headers = {
			'Accept': 'application/json, text/javascript, */*; q=0.01',
			'X-Requested-With': 'XMLHttpRequest',
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
			'Content-Type': 'application/json'
		}

proxies = {}
# Uncomment the below to use a proxy or if you are getting TSL / SSL error
# proxies = {
# 				'http': 'http://127.0.0.1:8080',
# 				'https': 'http://127.0.0.1:8080'
# 			}

request = requests.Session()

def find_public_reports(url):
	try:
		req = request.get(url, proxies=proxies, headers=headers, verify=False)
		if req.status_code == 200:
			data = json.loads(req.text)
			reports = data['reports']
			for report in reports:
				if 'url' in report.keys():
					title = report['title']
					reportid = report['id']
					report_url = Base_url + report['url']
					print report_url
					# writing public reports to Mongo DB
					if db.reports.count({'reportid': reportid}) == 0:
						db.reports.insert({'reportid': reportid, 'title': title, 'report_url': report_url})
	except Exception as ae:
		pass

urls = []
url = Base_url + '/hacktivity?sort_type=popular&page=1&filter=type%3Aall&range=forever'
urls.append(url)

req = request.get(url, proxies=proxies, headers=headers, verify=False)
pages = int(json.loads(req.text)['pages'])

for x in xrange(2,pages):
	url = Base_url + '/hacktivity?sort_type=popular&page='+str(x)+'&filter=type%3Aall&range=forever'
	urls.append(url)

pool = ThreadPool(POOL_SIZE)
results = pool.map(find_public_reports,urls)
pool.close() 
pool.join() 

# Writing public report urls to Output file
old_reports = []
with open(Out_file, READ_MODE) as lines:
	for line in lines:
		old_reports.append(line)

if len(old_reports) == 0:
	f = open(Out_file, WRITE_MODE)
else:
	f = open(Out_file, APPEND_MODE)

for key in dictbugs:
	text = dictbugs[key] + "\n"
	if text not in old_reports:
		f.write(text)
if f:
	f.close()



