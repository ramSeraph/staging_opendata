import requests
import xmltodict
from bs4 import BeautifulSoup
import urllib3
import json
import os


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def getParsedContent(data):
	out={}
	soup=BeautifulSoup(data["#text"],"lxml")
	for i in soup.findAll("li"):
		i=i.findAll("span")
		out[i[0].text]=i[1].text
	return out

def getParsedArea(data):
	l=list(map(float,data.split(" ")))
	out=[]
	no=0
	while no<len(l):
		out.append([l[no+1],l[no]])
		no+=2
	return out

def getParsedPoint(data):
	l=list(map(float,data.split(" ")))
	out=[]
	no=0
	while no<len(l):
		out.append([l[no+1],l[no]])
		no+=2
	return out[0]


class WMS:
	def __init__(self,wmsBaseLink,layer,bbox,width=300,height=300,query=""):
		self.wmsBaseLink=wmsBaseLink
		self.layer=layer
		self.bbox=bbox
		self.width=width
		self.height=height
		self.query=query

	def getHttpData(self):
		params={
			"service":"WMS",
			"version":"1.1.1",
			"request":"GetMap",
			"layers":self.layer,
			"bbox":self.bbox,
			"width":self.width,
			"height":self.height,
			"srs":"EPSG:4326",
			"format":"application/atom xml"
		}

		if self.query!="":
			params["cql_filter"]=self.query

		res=requests.get(self.wmsBaseLink,params=params,verify=False)
		xmldata=xmltodict.parse(res.text)
		return xmldata

	def parsePolygons(self,data):
		geoJson={}
		for i in data["feed"]["entry"]:
			if "content" in i:
				geoJson[i["title"]]={
				"info":getParsedContent(i["content"]),
				"cord":[getParsedArea(i["georss:where"]["georss:polygon"])]
				}
			else:
				geoJson[i["title"]]["cord"].append(getParsedArea(i["georss:where"]["georss:polygon"]))
		return geoJson

	def parseLines(self,data):
		geoJson={}
		for i in data["feed"]["entry"]:
			if "content" in i:
				geoJson[i["title"]]={
				"info":getParsedContent(i["content"]),
				"cord":[getParsedArea(i["georss:where"]["georss:line"])]
				}
			else:
				geoJson[i["title"]]["cord"].append(getParsedArea(i["georss:where"]["georss:line"]))
		return geoJson

	def parsePoints(self,data):
		geoJson={}
		for i in data["feed"]["entry"]:
			if "content" in i:
				geoJson[i["title"]]={
				"info":getParsedContent(i["content"]),
				"cord":getParsedPoint(i["georss:where"]["georss:point"])
				}
			else:
				geoJson[i["title"]]["cord"].append(getParsedArea(i["georss:where"]["georss:point"]))
		return geoJson

	def generateJsonToGeoJson(self,data,_type):
		returnObj={"type": "FeatureCollection","features": []}
		for i in data:
			returnObj["features"].append({
				"type": "Feature",
				"properties": data[i]["info"],
				"geometry": {
				"type": _type,
				"coordinates": data[i]["cord"]
			}})
		return returnObj

	def downloadWmsAsGeoJson(self):
		print(f"Started downloading {self.layer} : ")
		try:
			httpJson = self.getHttpData()
			print("    : Download raw response")
			parsedJson=None
			try:
				parsedJson = self.parsePoints(httpJson)
				return self.generateJsonToGeoJson(parsedJson,"Point")
			except Exception as e:
				print("    : Unidentified points json || "+str(e))

			try:
				parsedJson = self.parseLines(httpJson)
				return self.generateJsonToGeoJson(parsedJson,"MultiLineString")
			except Exception as e:
				print("    : Unidentified lines json || "+str(e))

			try:
				parsedJson = self.parsePolygons(httpJson)
				return self.generateJsonToGeoJson(parsedJson,"Polygon")
			except Exception as e:
				print("    : Unidentified polygons json || "+str(e))

			if (parsedJson==None):
				print("    : Unidentified json or mixed json, failed to return json")

		except Exception as e:
			print("    : Failed to get data from request url: || "+str(e))

		return None

	def saveAsGeoJson(self,folder,file_name):
		geojson = self.downloadWmsAsGeoJson()

		if (geojson!=None):
			os.makedirs(folder, exist_ok=True)
			with open(f"{folder}/{file_name}.geojson","w") as f:
				json.dump(geojson,f)
			print(f"    : Saved File as {folder}/{file_name}.geojson")
		else:
			print("    : Unable to create GeoJson")
		print("-"*50)