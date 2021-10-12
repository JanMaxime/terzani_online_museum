# Terzani Online Museum

## About

This project aims to bring the Terzani Photo collection online enabling text search and image search in the photo collection.

## Database Setup

This project uses a NoSQL database provided by MongoDb. Thus it is advised the users to create a [cloud Database](https://www.mongodb.com/pricing) and provide its URI as described below.

### Database Indexing

After the python script uploads the data to the database, to perform text base search the tag collection requires a search index.  A search index can be created on the collection using at steps shown [here](https://docs.atlas.mongodb.com/reference/atlas-search/create-index). After step 6, replace the JSON document with the below document and continue with the remaining steps.

```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "tag": [
        {
          "foldDiacritics": false,
          "maxGrams": 7,
          "minGrams": 3,
          "tokenization": "edgeGram",
          "type": "autocomplete"
        },
        {
          "analyzer": "lucene.standard",
          "multi": {
            "keywordAnalyzer": {
              "analyzer": "lucene.keyword",
              "type": "string"
            }
          },
          "type": "string"
        }
      ]
    }
  }
}
```

## Environment Variables

### To use GOOGLE VISION API

To use the google vision api to retrive annotaions, the user has to provide the API credentials as `GOOGLE_APPLICATION_CREDENTIALS` in a `.env` file.

### To use website and upload the annotations to database

To use the online monogo db service to retrive data or upload data, the user has to provide the API credentials as `MONGO_URI` in a `.env` file.

## Installation

### Install the requirements

The following project requires python>=3.8

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
pip install -r requirements.txt
```

Setup the project

```bash
python setup.py install
```

## Usage

### Photo annotation

The photo annotation on a collection can be performed using the `create_database.py` script in the `scripts/dataprocessing` directory. A Json configuration file should be provided to run the script.

#### Configuration File Format

```json
{
  "data_folder": "<folder to store data>",
  "scrap_image_iiif": "<Boolean to indicate if the image information needs to be scraped from a IIIF server>",
  "collection_url": "<URL of the collection>",
  "unsupported_collections": "<List of (string) collection ids to be neglected>",
  "col_cntry_json": "<Path to a Json file providing country mapping to each collection>",
  "server": "<The URL of the IIIF server containing the collection>",
  "manifest": "<Path to the manifest Json in the server>",
  "annotate_iiif": "<Boolean to indicate if the image needs to be annotated using Vison API>",
  "update_db": "<Boolean to indicate if the database needs to be updated>",
  "db_name": "<Name of the Mongo Database>",
  "tag_collection_name": "<Name of the Image tag collection in Mongo Database>",
  "annotation_collection_name": "<Name of the Image annotation collection in Mongo Database>",
  "fvector_collection_name": "<Name of the Image feature vector collection in Mongo Database>",
  "nu_photos": "<Number of images to be processed. If left empty or is set as 'full' all images are processed. If a number is provided, those many images are randomly sampled from the collection>"
}
```

#### Running script

```bash
python scripts/dataprocessing/create_database.py -c "./config.json"
```

### Website

The following components in the `server` present at _website/server.py_ needs to be changed according to the usage.

1. sample_annotations = mongo.db["Name of the Mongo collection containg the annotations"]
2. sample_tags = mongo.db["Name of the Mongo collection containg the taggings"]
3. sample_imageVectors = mongo.db["Name of the Mongo collection containg the feature vectors"]

#### Running script

```bash
python website/server.py
```

#### Errors

In case of error on the website, the should restart the server.


#### Caution on using the Image Colorization

We have observed that the python script sometimes fails to download the pretrained model for colorization. In such cases, the users are required to download the pth file from [here](https://www.dropbox.com/s/usf7uifrctqw9rl/ColorizeStable_gen.pth?dl=0) and place it in `website/DeOldify/models/` with the name `ColorizeStable_gen.pth`.
