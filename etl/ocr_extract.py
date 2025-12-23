import os
from azure.storage.blob import BlobServiceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import json

load_dotenv("./config/.env")

def get_blob_client():
    conn_str = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={os.getenv('STORAGE_ACCOUNT_NAME')};"
        f"AccountKey={os.getenv('STORAGE_ACCOUNT_KEY')};"
        f"EndpointSuffix=core.windows.net"
    )
    return BlobServiceClient.from_connection_string(conn_str)

def get_doc_client():
    return DocumentAnalysisClient(
        endpoint=os.getenv("FORM_RECOGNIZER_ENDPOINT"),
        credential=AzureKeyCredential(os.getenv("FORM_RECOGNIZER_KEY"))
    )

def extract_ocr(blob_name):
    blob_client = get_blob_client()
    container = blob_client.get_container_client(os.getenv("STORAGE_CONTAINER"))
    blob = container.get_blob_client(blob_name)

    stream = blob.download_blob().readall()
    doc_client = get_doc_client()

    poller = doc_client.begin_analyze_document(
        "prebuilt-read", stream
    )
    result = poller.result()

    return result.to_dict()

def main():
    blob_client = get_blob_client()
    container = blob_client.get_container_client(os.getenv("STORAGE_CONTAINER"))

    os.makedirs("data_samples/ocr_outputs", exist_ok=True)

    for blob in container.list_blobs():
        print(f"OCR processing: {blob.name}")
        ocr_result = extract_ocr(blob.name)

        out_file = f"data_samples/ocr_outputs/{blob.name}.json"
        with open(out_file, "w") as f:
            json.dump(ocr_result, f, indent=2)

if __name__ == "__main__":
    main()