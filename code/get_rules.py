import requests
import json
import sys
import os
import csv


OUTPUT_FILE = 'output.csv'

CC_REGIONS = [
    'eu-west-1',
    'ap-southeast-2',
    'us-west-2',
]

INCLUDED_HEADERS = [
    'provider',
    'id',
    'description',
    'package',
    'title',
    'name',
    'level',
    'risk-level',
    'release-date',
    'update-date',
    'knowledge-base-html',
    'multi-risk-level',
    'must-be-configured',
    'customisable',
    'not-scored',
    'requires-all-descriptors',
    'primary-descriptors',
    'secondary-descriptors',
    'has-cost-and-waste',
    'organisation',
]

INCLUDED_RULE_CATEGORIES = ['security', 'reliability', 'performance-efficiency', 'cost-optimisation',
                            'operational-excellence']


class CcRules:
    def __init__(self):

        try:
            print('Obtaining required environment variables...')
            self.cc_region = os.environ['CC_REGION'].lower()

            if self.cc_region not in CC_REGIONS:
                sys.exit('Error: Please ensure "CC_REGIONS" is set to a region which is supported by Cloud Conformity')

            self.api_key = os.environ['CC_API_KEY']

        except KeyError:
            sys.exit('Error: Please ensure all environment variables are set')

    def get_rules(self):
        cfn_scan_endpoint = f'https://ap-southeast-2-api.cloudconformity.com/v1/services/'

        headers = {
            'Content-Type': 'application/vnd.api+json',
            'Authorization': 'ApiKey ' + self.api_key
        }

        resp = requests.get(cfn_scan_endpoint, headers=headers)
        resp_json = json.loads(resp.text)
        json_output = json.dumps(resp_json, indent=4, sort_keys=True)

        return resp_json

    @staticmethod
    def process_included_categories(rule_entry):
        new_rule_entries = {}

        for rule_type in INCLUDED_RULE_CATEGORIES:
            if rule_type in rule_entry['categories']:
                new_rule_entries[rule_type] = 'YES'

            else:
                new_rule_entries[rule_type] = 'NO'

        del rule_entry['categories']
        return new_rule_entries

    def _process_included_rules(self, included_rules):
        num_included = len(included_rules)
        print(f'Found {num_included} included rules')

        for entry in included_rules:
            updated_categories = self.process_included_categories(entry)
            entry.update(updated_categories)

            kb_url = self._generate_kb_url(entry)
            entry['knowledge-base-html'] = kb_url

    @staticmethod
    def _generate_kb_url(rule_entry):
        base_url = 'https://www.cloudconformity.com/knowledge-base'
        provider = rule_entry['provider']
        id_entry = rule_entry['id']
        id_name = id_entry.split('-')[0]
        endpoint_name = rule_entry['knowledge-base-html']

        url_wo_extension = '/'.join([base_url, provider, id_name, endpoint_name])
        url = f'{url_wo_extension}.html'

        return url

    def generate_included_csv(self, headers, included_rules, filename=OUTPUT_FILE):
        self._process_included_rules(included_rules)
        self._join_included_csv_headers()

        with open(filename, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(included_rules)

        print(f'Created {OUTPUT_FILE}')

    @staticmethod
    def _join_included_csv_headers(insert_categories_after='risk-level'):
        insert_behind_index = INCLUDED_HEADERS.index(insert_categories_after)
        add_index = insert_behind_index + 1

        for idx, entry in enumerate(INCLUDED_RULE_CATEGORIES):
            new_entry_index = add_index + idx
            INCLUDED_HEADERS.insert(new_entry_index, entry)


def main():
    cc = CcRules()
    all_rules = cc.get_rules()
    included_rules = all_rules['included']
    cc.generate_included_csv(INCLUDED_HEADERS, included_rules)


if __name__ == '__main__':
    main()