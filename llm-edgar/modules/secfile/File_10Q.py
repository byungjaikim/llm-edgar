
import re
import json
import os

from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import StrOutputParser

from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from langchain.schema.runnable import RunnablePassthrough
from langchain.output_parsers import PydanticOutputParser
from langchain.pydantic_v1 import BaseModel, Field

import yfinance as yf

class SECRunner_Dashboard_10Q:

    def __init__(self, marker_endpage = '-'*80,
                 model_name = 'gpt-3.5-turbo-1106', temperature=0.0,
                 chunk_size_page=5000, chunk_size_text=1000, chunk_overlap_text=100):

        self.marker_endpage = marker_endpage
        self.model = ChatOpenAI(model_name=model_name, openai_api_key=os.getenv('OPENAI_API_KEY'), 
                                temperature=temperature)

        self.embedding_function = OpenAIEmbeddings(openai_api_key=os.getenv('OPENAI_API_KEY'))
        self.chunk_size_page = chunk_size_page
        self.chunk_size_text = chunk_size_text
        self.chunk_overlap_text = chunk_overlap_text

        # key words are used to search the statements
        query_revenue = "[Based on the CONSOLIDATED STATEMENTS OF INCOME or OPERATIONS, Revenues, Costs, Expenses, Research, Sales] How much is the total revenue of this company in this quarter (three months ended)? Report as a number with no digits omitted. For examples, 1000 in thousands is 1000000 and 1000 in millions is 1000000000"
        query_income = "[Based on the CONSOLIDATED STATEMENTS OF INCOME or OPERATIONS, Revenues, Costs, Expenses, Research, Sales] How much is the Net Income or Net loss of this company in this quarter (three months ended)? Report as a number with no digits omitted. For examples, 1000 in thousands is 1000000 and 1000 in millions is 1000000000"
        self.queries = {'Revenue': query_revenue, 'Income or Loss': query_income}

    def load_file(self, file_path):

        f = open(file_path)
        data = json.load(f)

        return data
    
    def make_retriever(self, document):

        # feature embedding
        page_splitter1 = CharacterTextSplitter(separator = self.marker_endpage, chunk_size=self.chunk_size_page, chunk_overlap=0)
        text_splitter2 = CharacterTextSplitter(separator = "\n\n", chunk_size=self.chunk_size_text, chunk_overlap=self.chunk_overlap_text)

        chunks = []
        pages = page_splitter1.split_text(document)
        for page in pages:
            splits = text_splitter2.split_text(page)
            chunks.extend(splits)

        db = Chroma.from_texts(chunks, self.embedding_function)

        return db

    def gpt_extract_financials(self, query, db):

        def format_docs(docs):
            #return docs[0].page_content
            return "\n\n".join([d.page_content for d in docs[:2]])

        retriever = db.as_retriever()

        # langchain for data extractor
        template_extract = """Answer the question based only on the following context:\n\n{context}\n\nQuestion: {question}"""
        prompt_extract = ChatPromptTemplate.from_template(template_extract)
        chain_extract = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()} 
            | prompt_extract
            | self.model
            | StrOutputParser()
        )
        data_str = chain_extract.invoke(query)

        return data_str

    def gpt_transform_format_to_json(self, data_str):

        class Financials(BaseModel):
            item: str = Field(description="the name of a financial item. SELECT one of the item list, delimited by triple backticks '''['Revenue','Income or Loss']'''.")
            value: int = Field(description="the number of the financial item which is reported. In case of '''Income or Loss''' item, the number should be negative in Loss or should be positive in Income. Report as a number with no digits omitted. For examples, 1000 in thousands is 1000000 and 1000 in millions is 1000000000")

        parser = PydanticOutputParser(pydantic_object=Financials)
        template_tojson="""{data_str}\nConvert the above sentence to JASON instance, following the rules as below.\n{format_instructions}\n"""
        prompt_tojson = ChatPromptTemplate.from_template(template_tojson)
        chain_tojson = (
            prompt_tojson
            | self.model
            | StrOutputParser()
        )

        data_json = chain_tojson.invoke({"format_instructions": parser.get_format_instructions(), "data_str": data_str} )
        data_json = json.loads(data_json)

        return data_json

    def get_data(self, file_path, date) -> dict:

        info_file = {}
        data = self.load_file(file_path)
        document = data['document_0']['merged']

        db = self.make_retriever(document)

        for key, query in self.queries.items():
            prompt_date = f' [the file report date: {date}] '

            financial_str = self.gpt_extract_financials(prompt_date + query, db)
            financial_str = '```' + key + '```' + ' - ' + financial_str
            financial_json = self.gpt_transform_format_to_json(financial_str)
            print(financial_str)
            if key != financial_json['item']:
                print("Key Error for extracted json data")
                assert False
            info_file[financial_json['item']] = financial_json['value']
        
        print(info_file)

        return info_file
