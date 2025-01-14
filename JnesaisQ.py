# !/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import re
import sys
from collections import namedtuple
from contextlib import contextmanager

__author__ = "Erik Pohl"
__copyright__ = "None"
__credits__ = ["Erik Pohl"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Erik Pohl"
__email__ = "erik.pohl.444@gmail.com"
__status__ = "Beta"

# todo : handle parameters which are attributes better
# todo : address complicated clauses
# (this clause AND this clause) OR (This clause AND this clause)
# OR (this clause)
# Ultimately a json query grammar
# With findings in json format


@contextmanager
def jnesaisq_compare(
        json_query_clause
):
    jnesaiq_instance = JnesaisQ(
        json_query_clause
    )
    yield_fun = jnesaiq_instance.is_this_a_full_match
    yield yield_fun


class JnesaisQ:
    """
    JnesaisQ
    Allows you to create a search term in JSON, and then apply that search term
    to JSON inputs to see if and where matches or mismatches occur.
    """

    def __init__(self, json_query_clause):
        self._json_query_finding = namedtuple(
            'json_query_finding',
            'current_json_path, actual_finding_value'
        )
        self._json_query_final_results = namedtuple(
            'json_query_results',
            'json_query_mismatches, json_query_matches'
        )
        self._JSON_KEY_MISSING = 'JSON_key_not_found'
        self._JSON_VALUE_MISMATCH = 'JSON_value_mismatch'
        self.JSON_query_clause = json_query_clause
        self._AND_match = 'AND_match'
        self._AND_mismatch = 'AND_mismatch'
        self._OR_match_mismatch = 'OR_match_mismatch'

    def compare_verbose(self, json_to_query, json_query_clause=None,
                        *,
                        debug_mode=False,
                        current_json_path='',
                        jnesais_q_matches=None,
                        jnesais_q_mismatches=None):
        """
        compare_json_to_query_clause
        :param json_to_query: This is an input JSON which you want to query
        :param json_query_clause: This is a clause in JSON format for
        the keys you want to query with values in regex
        :param debug_mode: Debug mode can be on or off, deprecated
        :param current_json_path: This is an internal only variable
        which tracks the current JSON path for reporting findings
        :param jnesais_q_matches: stores results of the matches
        identified by the query
        :param jnesais_q_mismatches: stores results of the mismatches identified
        by the query
        :return: This returns findings based on the JSON_to_query,
        the JSON_query_clause, and the match_mode
        """
        if not json_query_clause:
            json_query_clause = self.JSON_query_clause
        if jnesais_q_matches is None:
            jnesais_q_matches = []
        if jnesais_q_mismatches is None:
            jnesais_q_mismatches = []
        if debug_mode:
            logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        if not isinstance(json_query_clause, dict) and not isinstance(json_query_clause, list):
            if re.match(json_query_clause, json_to_query):
                jnesais_q_matches.append(
                    self._json_query_finding(
                        current_json_path,
                        json_to_query
                    )
                )
            else:
                jnesais_q_mismatches.append(
                    self._json_query_finding(
                        current_json_path,
                        self._JSON_VALUE_MISMATCH
                    )
                )
        else:    
            for format_key in json_query_clause.keys():
                current_json_path = current_json_path + '/' + format_key
                try:
                    json_to_query_key_value = json_to_query[format_key]
                except KeyError:
                    # key not found in JSON to query, so it is a mismatch
                    jnesais_q_mismatches.append(
                        self._json_query_finding(
                            current_json_path,
                            self._JSON_KEY_MISSING
                        )
                    )
                    continue
                json_query_key_value = json_query_clause[format_key]
                # if the format value which is being compared with
                # the test value is itself a clause, recurse
                if (
                        isinstance(json_query_key_value, list)
                        and
                        isinstance(json_to_query_key_value, list)
                ) or isinstance(json_query_key_value, dict):
                    if isinstance(json_query_key_value, list):
                        _ = self.compare_verbose(
                            json_to_query_key_value[0],
                            json_query_clause=json_query_key_value[0],
                            current_json_path=current_json_path,
                            jnesais_q_matches=jnesais_q_matches,
                            jnesais_q_mismatches=jnesais_q_mismatches,
                            debug_mode=debug_mode
                        )
                    else:
                        _ = self.compare_verbose(
                            json_to_query_key_value,
                            json_query_clause=json_query_key_value,
                            current_json_path=current_json_path,
                            jnesais_q_matches=jnesais_q_matches,
                            jnesais_q_mismatches=jnesais_q_mismatches,
                            debug_mode=debug_mode
                        )
                elif isinstance(json_to_query_key_value, list) and not isinstance(json_query_key_value, list):
                    jnesais_q_mismatches.append(
                            self._json_query_finding(
                                current_json_path,
                                self._JSON_VALUE_MISMATCH
                            )
                        )
                else:
                    if re.match(json_query_key_value, json_to_query_key_value):
                        jnesais_q_matches.append(
                            self._json_query_finding(
                                current_json_path,
                                json_to_query_key_value
                            )
                        )
                    else:
                        jnesais_q_mismatches.append(
                            self._json_query_finding(
                                current_json_path,
                                self._JSON_VALUE_MISMATCH
                            )
                        )
        return self._json_query_final_results(
            jnesais_q_mismatches,
            jnesais_q_matches
        )

    def overall_result(self, match_tuple):
        """
        overall_result
        Returns a diagnosis of the JSON format match attempt:
        AND_match, OR_match_mismatch, AND_mismatch
        :param match_tuple: this is the output of JnesaisQ.compare
        :return: an overall result
        """
        retval = []
        if match_tuple.json_query_mismatches == [] \
                and match_tuple.json_query_matches == []:
            return None
        if not match_tuple.json_query_mismatches \
                and match_tuple.json_query_matches:
            retval.append(self._AND_match)
        if match_tuple.json_query_mismatches \
                and match_tuple.json_query_matches:
            retval.append(self._OR_match_mismatch)
        if match_tuple.json_query_mismatches \
                and not match_tuple.json_query_matches:
            retval.append(self._AND_mismatch)
        return retval

    def compare(self, json_to_query):
        return self.overall_result(
            self.compare_verbose(
                json_to_query=json_to_query
            )
        )

    def is_this_a_full_match(self, json_to_query):
        return json_to_query if self.overall_result(
            self.compare_verbose(
                json_to_query=json_to_query
            )) == [self._AND_match] else None

    def list_of_compares(self, list_of_json_to_query):
        """
        list of compares
        outputs comparisons using the current search setup for a list of JSON
        :param list_of_json_to_query: the list of JSON to apply the query to
        :return: list of matching JSON
        """
        output_list_of_dicts = []
        for JSON_to_query in list_of_json_to_query:
            if self.overall_result(
                    self.compare_verbose(json_to_query=JSON_to_query)
            ) in ([self._OR_match_mismatch], [self._AND_match]):
                output_list_of_dicts.append(JSON_to_query)
        return output_list_of_dicts
