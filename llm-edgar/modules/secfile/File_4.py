
import re
import json

class SECRunner_Dashboard_4:

    def __init__(self, marker_endpage = '-'*80):

        self.marker_endpage = marker_endpage

    def load_file(self, file_path):

        f = open(file_path)
        data = json.load(f)

        return data

    def parse_header_complete_txt(self, xml_content, sec_url):

        info_header = {}
        # owner name
        name = re.search(r'<rptOwnerName>(.*?)</rptOwnerName>', xml_content).group(1)
        info_header['name'] = name
        info_header['sec_url'] = sec_url

        relationship_section = re.search(r'<reportingOwnerRelationship>(.*?)</reportingOwnerRelationship>', xml_content, re.DOTALL).group(1)
        list_header = [[r'<isDirector>(.*?)</isDirector>', 'is_director'],
                       [r'<isOfficer>(.*?)</isOfficer>', 'is_officer'],
                       [r'<isTenPercentOwner>(.*?)</isTenPercentOwner>', 'is_ten_percent_owner'],
                       [r'<isOther>(.*?)</isOther>', 'is_other'],
                       [r'<officerTitle>(.*?)</officerTitle>', 'owner_title']]

        for header in list_header:
            item = re.search(header[0], relationship_section) 
            if item is not None:
                info_header[header[1]] = item.group(1)

        return info_header

    def parse_transactions_complete_txt(self, xml_content, info_header):

        list_type_transactions = [[r'<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>','0'],
                                  [r'<derivativeTransaction>(.*?)</derivativeTransaction>','1']]
        list_prop_transactions = [[r'<securityTitle>(.*?)</securityTitle>','title'],
                                  [r'<transactionDate>(.*?)</transactionDate>','date'],
                                  [r'<transactionCode>(.*?)</transactionCode>','code'],
                                  [r'<transactionAcquiredDisposedCode>(.*?)</transactionAcquiredDisposedCode>','type'],
                                  [r'<transactionShares>(.*?)</transactionShares>','shares'],
                                  [r'<transactionPricePerShare>(.*?)</transactionPricePerShare>','price']]

        list_info = []
        for type_trans in list_type_transactions:
            trans_blocks = re.findall(type_trans[0], xml_content, re.DOTALL)
            is_derviative = type_trans[1]

            for transaction in trans_blocks:
                info_1trans = info_header.copy()
                info_1trans['derivative'] = is_derviative
                
                for prop_trans in list_prop_transactions:
                    if prop_trans[1] == 'code':
                        item = re.search(prop_trans[0], transaction, re.DOTALL)
                        info_1trans[prop_trans[1]] = item.group(1)
                    else:
                        item = re.search(prop_trans[0], transaction, re.DOTALL)
                        item_value = re.search(r'<value>(.*?)</value>', item.group(1))
                        if item_value is not None:
                            info_1trans[prop_trans[1]] = item_value.group(1)
                        else:
                            info_1trans[prop_trans[1]] = None         
                list_info.append(info_1trans)

        return list_info                       

    def get_data(self, file_path, sec_url) -> list:

        data = self.load_file(file_path)

        # read complete txt file in data
        document_text = data['document_txt']
        # Extract the XML portion from the provided text
        xml_content = re.search(r'<XML>(.*?)</XML>', document_text, re.DOTALL).group(1)

        # parse header 
        info_header = self.parse_header_complete_txt(xml_content, sec_url)
        # parse transaction
        list_info = self.parse_transactions_complete_txt(xml_content, info_header)

        return list_info





