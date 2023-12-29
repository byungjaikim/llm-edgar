
import re
import json
import os

from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import StrOutputParser

class SECRunner_Dashboard_8K:

    def __init__(self, marker_endpage = '-'*80, skip_firstpage_mainhtm = True,
                 maxlen_llminput = 15000, company_name = None, type_of_summary_source='text',
                 model_name = 'gpt-3.5-turbo-1106', temperature=0.0):

        self.marker_endpage = marker_endpage
        self.skip_firstpage_mainhtm = skip_firstpage_mainhtm
        self.maximum_len = maxlen_llminput
        self.company_name = company_name
        self.type_of_summary_source = type_of_summary_source

        self.model = ChatOpenAI(model_name=model_name, openai_api_key=os.getenv('OPENAI_API_KEY'), 
                                temperature=temperature)

    def load_file(self, file_path):

        f = open(file_path)
        data = json.load(f)

        return data

    def gpt_summarize(self, content):
        
        prompt = PromptTemplate.from_template('Your task is to generate a summary of a SEC edgar file to give insight to investor.' \
                                              '\n\n```{content}```\n\nSummarize the above content, delimited by triple backticks. '\
                                              'Include all factual information, numbers, stats etc if available.')

        chain = prompt | self.model | StrOutputParser()
        response = chain.invoke({"content": content})

        return response

    def select_htmpart(self, content, is_firstpage=False):

        if is_firstpage and self.skip_firstpage_mainhtm:
            content_pages = content.split(self.marker_endpage)
            content = self.marker_endpage.join(content_pages[1:])   
        content = content[:self.maximum_len]

        return content

    def summarize_htmfiles(self, data, type_of_summary_source = 'text'):

        """
        data (dict): loaded documents 
        type_of_summary_source (str): "text", "table", "merged"
        """
        summary_all = {}
        for key in data.keys():
            is_firstpage = True if key == 'document_0' else False

            data_doc = data[key]
            content = data_doc[type_of_summary_source]
            content = self.select_htmpart(content, is_firstpage=is_firstpage)
            summary = self.gpt_summarize(content)
            
            summary_all[key] = summary
        
        return summary_all

    def gpt_writer(self, content, html_format):

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "Your primary goal is to write a comprehensive financial article, based on provided EDGAR file of {company_name}"),
                ("human", '```{content}``` Using the above facts and events of {company_name}, delimited by triple backticks, '\
                                'write a blog article in html format. Here are ground rules'\
                                '1. The format is html format. The overall structure is provided below, delimited by <html> and </html>'\
                                '2. write the title of this article in the section of <title>.'\
                                '3. write the main paragraphs in the section of <article>.'\
                                '4. The main paragrpahs are well structed and informative including subtitle or bullet points (with facts and numbers if available.)'\
                                '5. DO NOT modify other parts in the provided html form'\
                                '6. Your answer should be html code without other responses'\
                                'The html format = '\
                                '{structure}'),
            ]
        )

        chain = prompt | self.model | StrOutputParser()
        response = chain.invoke({"content": content, "structure": html_format, "company_name": self.company_name})

        return response

    def gpt_html_translator_to_kor(self, content):

        prompt = ChatPromptTemplate.from_messages(
            [
                ("human", 'Translate the texts in the html code into Korean, delimited by triple backticks'\
                          'Here are ground rules: '\
                          '1. Translate the texts in the sections of <title> and <article>'\
                          '2. Proper noun such as company name or economic terminology should be in English.' \
                          '3. ONLY translate texts and replace them in html code. Provided html format and structure SHOULD be maintained' \
                          '4. The response shoud be only html code without other responses'\
                          '```{content}```'),
            ]
        )

        chain = prompt | self.model | StrOutputParser()
        response = chain.invoke({"content": content})

        return response

    def write_post(self, data):
        """
        data (dict): summarized documents
        """
        contents = []
        for v in data.values():
            contents.append(v)
        contents = '\n\n'.join(contents)
        contents = contents[:self.maximum_len]

        basic_html_format = "<html>\n<head>\n<title></title>\n</head>\n<body>\n<article></article>\n</body>\n</html>"
        post = self.gpt_writer(contents, basic_html_format)

        # strip the output with html
        html_start = post.find('<html>')
        html_end = post.find('</html>')
        if html_start != -1 and html_end != -1:
            post = post[html_start : html_end + len('</html>')]
        else:
            post = None

        return post

    def translate_post(self, post, lang='Kor'):
        """
        data (dict): summarized documents
        """
        if lang == 'Kor':
            post = self.gpt_html_translator_to_kor(post)
        else:
            # TODO: other languages
            assert False

        # strip the output with html
        html_start = post.find('<html>')
        html_end = post.find('</html>')
        if html_start != -1 and html_end != -1:
            post = post[html_start : html_end + len('</html>')]
        else:
            post = None

        return post

    def get_data(self, file_path) -> dict:

        data = self.load_file(file_path)
        data.pop('document_txt')

        fname = file_path.split('_')[-1].split('.')[0]
        folder_path = os.path.dirname(file_path)
        info_file = {}

        # summarize each documents
        output_summary_path = os.path.join(folder_path, 'form8k_summary_{}.json'.format(fname))
        if not os.path.exists(output_summary_path):  

            summary_all = self.summarize_htmfiles(data, self.type_of_summary_source)

            with open(output_summary_path, "w") as json_file:
                json.dump(summary_all, json_file)
        else:
            f = open(output_summary_path)
            summary_all = json.load(f)
        info_file['summary_path'] = output_summary_path

        # write a summarized post
        output_post_path = os.path.join(folder_path, 'form8k_post_{}.json'.format(fname))
        if not os.path.exists(output_post_path):  

            post = self.write_post(summary_all)

            if post:
                with open(output_post_path, "w") as json_file:
                    json.dump(post, json_file)
        else:
            f = open(output_post_path)
            post = json.load(f)
        info_file['post_path'] = output_post_path

        # translate a summarized post into Korean
        output_postkor_path = os.path.join(folder_path, 'form8k_postkor_{}.json'.format(fname))
        if not os.path.exists(output_postkor_path):  

            post_kor = self.translate_post(post, lang='Kor')

            if post_kor:
                with open(output_postkor_path, "w") as json_file:
                    json.dump(post_kor, json_file)
        # else:
        #     f = open(output_postkor_path)
        #     post_kor = json.load(f)
        info_file['postkor_path'] = output_postkor_path

        return info_file
