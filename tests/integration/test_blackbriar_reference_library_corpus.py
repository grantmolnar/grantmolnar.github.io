"""Blackbriar Hall reference defragmentation and preservation evidence."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode
from uuid import UUID

import pytest

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.support.corpus_contracts import assert_rendered_documents_match
from tests.support.web import build_authoring_app, build_play_app, request_wsgi

pytestmark = pytest.mark.corpus
BLACKBRIAR_ROOT = Path("examples/the-witch-of-blackbriar-hall")
JUDITH_ID = 'fc38cc24-165f-4df6-bf04-7813911d6b8d'
YSRA_ID = '7dc115f7-e717-427c-ba9b-33f28fbd2364'
CALDUS_ID = '1ab6d356-b394-4528-b5c5-0530f8d56a65'
MARA_ID = '9123fa4b-e1bd-45c7-acf2-7656663ee5b3'
NELL_ID = '24f7323c-e560-49a1-8f44-95c715c2a2d0'
TOMAS_ID = '69daecdb-c3fe-4aab-99ad-4a9feafe9720'
PELL_ID = 'd23d66ad-f4d2-46c3-b62d-68d7dc725cca'
ODO_ID = 'a356a5b7-8460-49ac-85ec-593b435280f7'
CLEFT_ID = '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1'
HARL_ID = '03ef5b0b-c002-4f38-9a3b-47a03a379e8d'
CORIN_ID = 'adb089a8-d281-4d33-beaa-74629823bc6a'
GARRAN_ID = 'd8e9dfa9-6c79-43e3-b8ca-e645c023469c'
MERCY_HOUSE_ID = '426ebd86-3426-4b5a-b2ce-1b6c09b43e68'
HALL_ID = 'b2bfc545-8e6b-446b-a961-fe60db81ffc9'
REFUGE_ID = '46c9f075-d08e-4251-8fba-c86f47b30411'
PITS_ID = '9588d099-9c55-4750-b5f6-271d63b32456'
CHAPEL_ID = 'e2455050-3963-46d2-8736-0dd826037218'
MERE_ID = '2fe9af67-c2c0-49d4-b491-a7d220b3c95e'
CROW_WOOD_ID = 'b4ac4a8e-4b89-4bd9-a9b1-4ffe2274f9eb'
UNDERHALL_ID = 'bae1dfda-a1f6-468a-a083-be9ebb6057ee'
BLACKTHORN_ID = 'd2957684-e1f2-405d-87f9-65521364f2cb'
COURT_ID = 'd119cb74-4f99-4e9a-8ae5-b500cfbe95f3'
GUEST_ID = '3a669960-c05d-4bd8-ae4b-33137d486977'
WORM_ID = '20388d1b-f4cb-40a7-b65f-686bb4e48be3'
CHILD_ID = '5d4b8115-88b1-4952-b4b1-1a67b35d3d8e'
MERCY_BOOK_ID = '4d5e6282-bbb2-481c-99d4-31e581fe1737'
TOKENS_ID = '91b081d9-3044-46e9-8b0e-a9e1db7624b3'
BELL_ID = 'c85a1b9d-90dd-4958-be4a-e0fc6eaca068'
VESSELS_ID = '9f7dfd7a-646b-4d48-86a2-684ac88398a0'

SESSION_ONE_REFERENCE_IDS = ('fc38cc24-165f-4df6-bf04-7813911d6b8d',
 '7dc115f7-e717-427c-ba9b-33f28fbd2364',
 '1ab6d356-b394-4528-b5c5-0530f8d56a65',
 '9123fa4b-e1bd-45c7-acf2-7656663ee5b3',
 '24f7323c-e560-49a1-8f44-95c715c2a2d0',
 '69daecdb-c3fe-4aab-99ad-4a9feafe9720',
 'd23d66ad-f4d2-46c3-b62d-68d7dc725cca',
 'a356a5b7-8460-49ac-85ec-593b435280f7',
 '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1',
 '03ef5b0b-c002-4f38-9a3b-47a03a379e8d')
SESSION_TWO_REFERENCE_IDS = ('adb089a8-d281-4d33-beaa-74629823bc6a',
 'd8e9dfa9-6c79-43e3-b8ca-e645c023469c',
 '426ebd86-3426-4b5a-b2ce-1b6c09b43e68',
 'b2bfc545-8e6b-446b-a961-fe60db81ffc9',
 '46c9f075-d08e-4251-8fba-c86f47b30411',
 '9588d099-9c55-4750-b5f6-271d63b32456',
 'e2455050-3963-46d2-8736-0dd826037218',
 '2fe9af67-c2c0-49d4-b491-a7d220b3c95e',
 'b4ac4a8e-4b89-4bd9-a9b1-4ffe2274f9eb',
 'bae1dfda-a1f6-468a-a083-be9ebb6057ee',
 'd2957684-e1f2-405d-87f9-65521364f2cb',
 'd119cb74-4f99-4e9a-8ae5-b500cfbe95f3',
 '3a669960-c05d-4bd8-ae4b-33137d486977',
 '20388d1b-f4cb-40a7-b65f-686bb4e48be3',
 '5d4b8115-88b1-4952-b4b1-1a67b35d3d8e',
 '4d5e6282-bbb2-481c-99d4-31e581fe1737',
 '91b081d9-3044-46e9-8b0e-a9e1db7624b3',
 'c85a1b9d-90dd-4958-be4a-e0fc6eaca068',
 '9f7dfd7a-646b-4d48-86a2-684ac88398a0')
REFERENCE_IDS = SESSION_ONE_REFERENCE_IDS + SESSION_TWO_REFERENCE_IDS
SESSION_ONE_LINKS = {'saint-orra-gallows': ('fc38cc24-165f-4df6-bf04-7813911d6b8d',
                        '7dc115f7-e717-427c-ba9b-33f28fbd2364',
                        '1ab6d356-b394-4528-b5c5-0530f8d56a65',
                        '9123fa4b-e1bd-45c7-acf2-7656663ee5b3',
                        '24f7323c-e560-49a1-8f44-95c715c2a2d0',
                        '69daecdb-c3fe-4aab-99ad-4a9feafe9720',
                        'd23d66ad-f4d2-46c3-b62d-68d7dc725cca',
                        'a356a5b7-8460-49ac-85ec-593b435280f7',
                        '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1'),
 'sedge-croft': ('fc38cc24-165f-4df6-bf04-7813911d6b8d',
                 '1ab6d356-b394-4528-b5c5-0530f8d56a65',
                 '9123fa4b-e1bd-45c7-acf2-7656663ee5b3',
                 '24f7323c-e560-49a1-8f44-95c715c2a2d0',
                 '69daecdb-c3fe-4aab-99ad-4a9feafe9720',
                 'd23d66ad-f4d2-46c3-b62d-68d7dc725cca',
                 'a356a5b7-8460-49ac-85ec-593b435280f7',
                 '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1'),
 'saint-mercy-house': ('fc38cc24-165f-4df6-bf04-7813911d6b8d',
                       '7dc115f7-e717-427c-ba9b-33f28fbd2364',
                       '1ab6d356-b394-4528-b5c5-0530f8d56a65',
                       '9123fa4b-e1bd-45c7-acf2-7656663ee5b3',
                       '24f7323c-e560-49a1-8f44-95c715c2a2d0',
                       '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1',
                       '03ef5b0b-c002-4f38-9a3b-47a03a379e8d'),
 'blackbriar-hall': ('fc38cc24-165f-4df6-bf04-7813911d6b8d',
                     '7dc115f7-e717-427c-ba9b-33f28fbd2364',
                     '1ab6d356-b394-4528-b5c5-0530f8d56a65',
                     '9123fa4b-e1bd-45c7-acf2-7656663ee5b3',
                     '24f7323c-e560-49a1-8f44-95c715c2a2d0',
                     'd23d66ad-f4d2-46c3-b62d-68d7dc725cca',
                     'a356a5b7-8460-49ac-85ec-593b435280f7',
                     '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1',
                     '03ef5b0b-c002-4f38-9a3b-47a03a379e8d'),
 'burned-refuge': ('fc38cc24-165f-4df6-bf04-7813911d6b8d',
                   '1ab6d356-b394-4528-b5c5-0530f8d56a65',
                   '9123fa4b-e1bd-45c7-acf2-7656663ee5b3',
                   '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1'),
 'white-pits': ('fc38cc24-165f-4df6-bf04-7813911d6b8d',
                '1ab6d356-b394-4528-b5c5-0530f8d56a65',
                '9123fa4b-e1bd-45c7-acf2-7656663ee5b3',
                'd23d66ad-f4d2-46c3-b62d-68d7dc725cca',
                '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1',
                '03ef5b0b-c002-4f38-9a3b-47a03a379e8d'),
 'chapel-of-the-free-witness': ('fc38cc24-165f-4df6-bf04-7813911d6b8d',
                                '7dc115f7-e717-427c-ba9b-33f28fbd2364',
                                '1ab6d356-b394-4528-b5c5-0530f8d56a65',
                                '9123fa4b-e1bd-45c7-acf2-7656663ee5b3',
                                '24f7323c-e560-49a1-8f44-95c715c2a2d0',
                                'a356a5b7-8460-49ac-85ec-593b435280f7',
                                '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1'),
 'moonless-mere': ('fc38cc24-165f-4df6-bf04-7813911d6b8d',
                   '9123fa4b-e1bd-45c7-acf2-7656663ee5b3',
                   '24f7323c-e560-49a1-8f44-95c715c2a2d0',
                   '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1',
                   '03ef5b0b-c002-4f38-9a3b-47a03a379e8d'),
 'crow-wood': ('fc38cc24-165f-4df6-bf04-7813911d6b8d',
               '24f7323c-e560-49a1-8f44-95c715c2a2d0',
               '69daecdb-c3fe-4aab-99ad-4a9feafe9720',
               '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1',
               '03ef5b0b-c002-4f38-9a3b-47a03a379e8d'),
 'underhall-of-the-hollow-feast': ('fc38cc24-165f-4df6-bf04-7813911d6b8d',
                                   '7dc115f7-e717-427c-ba9b-33f28fbd2364',
                                   '1ab6d356-b394-4528-b5c5-0530f8d56a65',
                                   '9123fa4b-e1bd-45c7-acf2-7656663ee5b3',
                                   '24f7323c-e560-49a1-8f44-95c715c2a2d0',
                                   '69daecdb-c3fe-4aab-99ad-4a9feafe9720',
                                   'd23d66ad-f4d2-46c3-b62d-68d7dc725cca',
                                   'a356a5b7-8460-49ac-85ec-593b435280f7',
                                   '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1',
                                   '03ef5b0b-c002-4f38-9a3b-47a03a379e8d')}
APPENDED_LINKS = {'saint-orra-gallows': ('b2bfc545-8e6b-446b-a961-fe60db81ffc9',
                        'e2455050-3963-46d2-8736-0dd826037218',
                        'd2957684-e1f2-405d-87f9-65521364f2cb',
                        'd119cb74-4f99-4e9a-8ae5-b500cfbe95f3',
                        '4d5e6282-bbb2-481c-99d4-31e581fe1737',
                        '91b081d9-3044-46e9-8b0e-a9e1db7624b3',
                        'c85a1b9d-90dd-4958-be4a-e0fc6eaca068'),
 'sedge-croft': ('adb089a8-d281-4d33-beaa-74629823bc6a',
                 '426ebd86-3426-4b5a-b2ce-1b6c09b43e68',
                 '2fe9af67-c2c0-49d4-b491-a7d220b3c95e',
                 'b4ac4a8e-4b89-4bd9-a9b1-4ffe2274f9eb',
                 '3a669960-c05d-4bd8-ae4b-33137d486977',
                 '5d4b8115-88b1-4952-b4b1-1a67b35d3d8e',
                 '91b081d9-3044-46e9-8b0e-a9e1db7624b3',
                 '9f7dfd7a-646b-4d48-86a2-684ac88398a0'),
 'saint-mercy-house': ('adb089a8-d281-4d33-beaa-74629823bc6a',
                       'd8e9dfa9-6c79-43e3-b8ca-e645c023469c',
                       '426ebd86-3426-4b5a-b2ce-1b6c09b43e68',
                       'b2bfc545-8e6b-446b-a961-fe60db81ffc9',
                       '2fe9af67-c2c0-49d4-b491-a7d220b3c95e',
                       'b4ac4a8e-4b89-4bd9-a9b1-4ffe2274f9eb',
                       'bae1dfda-a1f6-468a-a083-be9ebb6057ee',
                       'd2957684-e1f2-405d-87f9-65521364f2cb',
                       'd119cb74-4f99-4e9a-8ae5-b500cfbe95f3',
                       '20388d1b-f4cb-40a7-b65f-686bb4e48be3',
                       '5d4b8115-88b1-4952-b4b1-1a67b35d3d8e',
                       '4d5e6282-bbb2-481c-99d4-31e581fe1737',
                       '9f7dfd7a-646b-4d48-86a2-684ac88398a0'),
 'blackbriar-hall': ('adb089a8-d281-4d33-beaa-74629823bc6a',
                     'd8e9dfa9-6c79-43e3-b8ca-e645c023469c',
                     '426ebd86-3426-4b5a-b2ce-1b6c09b43e68',
                     'b2bfc545-8e6b-446b-a961-fe60db81ffc9',
                     '46c9f075-d08e-4251-8fba-c86f47b30411',
                     '9588d099-9c55-4750-b5f6-271d63b32456',
                     'b4ac4a8e-4b89-4bd9-a9b1-4ffe2274f9eb',
                     'bae1dfda-a1f6-468a-a083-be9ebb6057ee',
                     'd2957684-e1f2-405d-87f9-65521364f2cb',
                     'd119cb74-4f99-4e9a-8ae5-b500cfbe95f3',
                     '3a669960-c05d-4bd8-ae4b-33137d486977',
                     '20388d1b-f4cb-40a7-b65f-686bb4e48be3',
                     '5d4b8115-88b1-4952-b4b1-1a67b35d3d8e',
                     '4d5e6282-bbb2-481c-99d4-31e581fe1737',
                     '91b081d9-3044-46e9-8b0e-a9e1db7624b3',
                     '9f7dfd7a-646b-4d48-86a2-684ac88398a0'),
 'burned-refuge': ('46c9f075-d08e-4251-8fba-c86f47b30411',
                   'e2455050-3963-46d2-8736-0dd826037218',
                   'b4ac4a8e-4b89-4bd9-a9b1-4ffe2274f9eb',
                   'bae1dfda-a1f6-468a-a083-be9ebb6057ee',
                   'd2957684-e1f2-405d-87f9-65521364f2cb',
                   'd119cb74-4f99-4e9a-8ae5-b500cfbe95f3',
                   '3a669960-c05d-4bd8-ae4b-33137d486977',
                   'c85a1b9d-90dd-4958-be4a-e0fc6eaca068'),
 'white-pits': ('d8e9dfa9-6c79-43e3-b8ca-e645c023469c',
                '9588d099-9c55-4750-b5f6-271d63b32456',
                'e2455050-3963-46d2-8736-0dd826037218',
                'bae1dfda-a1f6-468a-a083-be9ebb6057ee',
                'd119cb74-4f99-4e9a-8ae5-b500cfbe95f3',
                '20388d1b-f4cb-40a7-b65f-686bb4e48be3',
                'c85a1b9d-90dd-4958-be4a-e0fc6eaca068'),
 'chapel-of-the-free-witness': ('426ebd86-3426-4b5a-b2ce-1b6c09b43e68',
                                '46c9f075-d08e-4251-8fba-c86f47b30411',
                                '9588d099-9c55-4750-b5f6-271d63b32456',
                                'e2455050-3963-46d2-8736-0dd826037218',
                                '2fe9af67-c2c0-49d4-b491-a7d220b3c95e',
                                'bae1dfda-a1f6-468a-a083-be9ebb6057ee',
                                'd119cb74-4f99-4e9a-8ae5-b500cfbe95f3',
                                '3a669960-c05d-4bd8-ae4b-33137d486977',
                                '20388d1b-f4cb-40a7-b65f-686bb4e48be3',
                                '5d4b8115-88b1-4952-b4b1-1a67b35d3d8e',
                                'c85a1b9d-90dd-4958-be4a-e0fc6eaca068',
                                '9f7dfd7a-646b-4d48-86a2-684ac88398a0'),
 'moonless-mere': ('adb089a8-d281-4d33-beaa-74629823bc6a',
                   '426ebd86-3426-4b5a-b2ce-1b6c09b43e68',
                   'b2bfc545-8e6b-446b-a961-fe60db81ffc9',
                   'e2455050-3963-46d2-8736-0dd826037218',
                   '2fe9af67-c2c0-49d4-b491-a7d220b3c95e',
                   'b4ac4a8e-4b89-4bd9-a9b1-4ffe2274f9eb',
                   'bae1dfda-a1f6-468a-a083-be9ebb6057ee',
                   '5d4b8115-88b1-4952-b4b1-1a67b35d3d8e',
                   '9f7dfd7a-646b-4d48-86a2-684ac88398a0'),
 'crow-wood': ('adb089a8-d281-4d33-beaa-74629823bc6a',
               'd8e9dfa9-6c79-43e3-b8ca-e645c023469c',
               '426ebd86-3426-4b5a-b2ce-1b6c09b43e68',
               'b2bfc545-8e6b-446b-a961-fe60db81ffc9',
               '46c9f075-d08e-4251-8fba-c86f47b30411',
               '9588d099-9c55-4750-b5f6-271d63b32456',
               '2fe9af67-c2c0-49d4-b491-a7d220b3c95e',
               'b4ac4a8e-4b89-4bd9-a9b1-4ffe2274f9eb',
               'bae1dfda-a1f6-468a-a083-be9ebb6057ee',
               'd2957684-e1f2-405d-87f9-65521364f2cb',
               '3a669960-c05d-4bd8-ae4b-33137d486977',
               '20388d1b-f4cb-40a7-b65f-686bb4e48be3',
               '5d4b8115-88b1-4952-b4b1-1a67b35d3d8e',
               '4d5e6282-bbb2-481c-99d4-31e581fe1737',
               '91b081d9-3044-46e9-8b0e-a9e1db7624b3',
               '9f7dfd7a-646b-4d48-86a2-684ac88398a0'),
 'underhall-of-the-hollow-feast': ('adb089a8-d281-4d33-beaa-74629823bc6a',
                                   'd8e9dfa9-6c79-43e3-b8ca-e645c023469c',
                                   '426ebd86-3426-4b5a-b2ce-1b6c09b43e68',
                                   'b2bfc545-8e6b-446b-a961-fe60db81ffc9',
                                   '46c9f075-d08e-4251-8fba-c86f47b30411',
                                   '9588d099-9c55-4750-b5f6-271d63b32456',
                                   'e2455050-3963-46d2-8736-0dd826037218',
                                   '2fe9af67-c2c0-49d4-b491-a7d220b3c95e',
                                   'b4ac4a8e-4b89-4bd9-a9b1-4ffe2274f9eb',
                                   'bae1dfda-a1f6-468a-a083-be9ebb6057ee',
                                   'd2957684-e1f2-405d-87f9-65521364f2cb',
                                   'd119cb74-4f99-4e9a-8ae5-b500cfbe95f3',
                                   '3a669960-c05d-4bd8-ae4b-33137d486977',
                                   '20388d1b-f4cb-40a7-b65f-686bb4e48be3',
                                   '5d4b8115-88b1-4952-b4b1-1a67b35d3d8e',
                                   '4d5e6282-bbb2-481c-99d4-31e581fe1737',
                                   '91b081d9-3044-46e9-8b0e-a9e1db7624b3',
                                   'c85a1b9d-90dd-4958-be4a-e0fc6eaca068',
                                   '9f7dfd7a-646b-4d48-86a2-684ac88398a0')}
EXPECTED_LINKS = {key: SESSION_ONE_LINKS[key] + APPENDED_LINKS[key] for key in SESSION_ONE_LINKS}
EXPECTED_COUNTS = {'fc38cc24-165f-4df6-bf04-7813911d6b8d': 10,
 '7dc115f7-e717-427c-ba9b-33f28fbd2364': 5,
 '1ab6d356-b394-4528-b5c5-0530f8d56a65': 8,
 '9123fa4b-e1bd-45c7-acf2-7656663ee5b3': 9,
 '24f7323c-e560-49a1-8f44-95c715c2a2d0': 8,
 '69daecdb-c3fe-4aab-99ad-4a9feafe9720': 4,
 'd23d66ad-f4d2-46c3-b62d-68d7dc725cca': 5,
 'a356a5b7-8460-49ac-85ec-593b435280f7': 5,
 '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1': 10,
 'b2bfc545-8e6b-446b-a961-fe60db81ffc9': 6,
 'e2455050-3963-46d2-8736-0dd826037218': 6,
 'd2957684-e1f2-405d-87f9-65521364f2cb': 6,
 'd119cb74-4f99-4e9a-8ae5-b500cfbe95f3': 7,
 '4d5e6282-bbb2-481c-99d4-31e581fe1737': 5,
 '91b081d9-3044-46e9-8b0e-a9e1db7624b3': 5,
 'c85a1b9d-90dd-4958-be4a-e0fc6eaca068': 5,
 'adb089a8-d281-4d33-beaa-74629823bc6a': 6,
 '426ebd86-3426-4b5a-b2ce-1b6c09b43e68': 7,
 '2fe9af67-c2c0-49d4-b491-a7d220b3c95e': 6,
 'b4ac4a8e-4b89-4bd9-a9b1-4ffe2274f9eb': 7,
 '3a669960-c05d-4bd8-ae4b-33137d486977': 6,
 '5d4b8115-88b1-4952-b4b1-1a67b35d3d8e': 7,
 '9f7dfd7a-646b-4d48-86a2-684ac88398a0': 7,
 '03ef5b0b-c002-4f38-9a3b-47a03a379e8d': 6,
 'd8e9dfa9-6c79-43e3-b8ca-e645c023469c': 5,
 'bae1dfda-a1f6-468a-a083-be9ebb6057ee': 8,
 '20388d1b-f4cb-40a7-b65f-686bb4e48be3': 6,
 '46c9f075-d08e-4251-8fba-c86f47b30411': 5,
 '9588d099-9c55-4750-b5f6-271d63b32456': 5}
SESSION_ONE_BODY_HASHES = {'fc38cc24-165f-4df6-bf04-7813911d6b8d': '7c2423998af28eeb0e992c239ced9be54deeee5f08a1a8d5ec5c1adaaa7d7d4d',
 '7dc115f7-e717-427c-ba9b-33f28fbd2364': '25e69824a80ec6864110c4ac84fa5f48d610a3f663775e23160569a68a2cda2c',
 '1ab6d356-b394-4528-b5c5-0530f8d56a65': '48e4af0db279f81c2e1a54176b6616c076647da20485073fe2503f59a416f382',
 '9123fa4b-e1bd-45c7-acf2-7656663ee5b3': 'abb11319ec1387790ecdaf2f0b6a9c0026397c5d554fbf5a675fe6e85774d6e6',
 '24f7323c-e560-49a1-8f44-95c715c2a2d0': 'e423987668f3ae60d18a6188afa1dad79df63ca1eb2b1b4fc040581cc490928e',
 '69daecdb-c3fe-4aab-99ad-4a9feafe9720': 'c818b59e24c53eb01a80316be3aab80986f2d251a79da05ff48527400ebd4017',
 'd23d66ad-f4d2-46c3-b62d-68d7dc725cca': '06128e557d985263166f122e69d93f1a68e8c02500440824e78a03bf26376806',
 'a356a5b7-8460-49ac-85ec-593b435280f7': 'e0b7580dfbdf555f056968fdd4e93b9a3171ffbbddb7aeed3cfd49a560c11490',
 '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1': '88a594e0ade17664ba9af6924f9cedbd503684e049b0a35a7a0c4729636ebfa9',
 '03ef5b0b-c002-4f38-9a3b-47a03a379e8d': '9815cae5a628c091fc7d33a327b41f4e8f9a3b6d79a65f212ad0c34a722f724c'}
SESSION_TWO_BODY_HASHES = {'adb089a8-d281-4d33-beaa-74629823bc6a': 'e2a479c54071b31d13c4126843a7fdd70bf0ca4ee65f066184e2c63f91063cc1', 'd8e9dfa9-6c79-43e3-b8ca-e645c023469c': '745c4e154dda3f4263065c4ada997ecb4e00ecc71662dbbad78f07e799d9e71c', '426ebd86-3426-4b5a-b2ce-1b6c09b43e68': '6975e49c4193a2ccbb81ca23a3d3ccf08b2cda26baf6d4c2131f571ee09e81d0', 'b2bfc545-8e6b-446b-a961-fe60db81ffc9': 'aa0a538adc248b22b2bd23ed42a88738598582127ae3f9f9841fb86157cd3df5', '46c9f075-d08e-4251-8fba-c86f47b30411': '4447a0b01fbb6b32e0824b2c96f1956e282841e629e03470430b50187338d8f3', '9588d099-9c55-4750-b5f6-271d63b32456': '7f15b0a6b34c9c85c13c5240de4d069d8ba394d4e0426cc9d550695e135162de', 'e2455050-3963-46d2-8736-0dd826037218': '8ee8e4ddfbaf984d877c39d0e498a2e268cb804221d6947af06180d21e929f9e', '2fe9af67-c2c0-49d4-b491-a7d220b3c95e': '50b611787795f96cd214486e44ee1098360e13a9e48934d4692dba7de934253f', 'b4ac4a8e-4b89-4bd9-a9b1-4ffe2274f9eb': 'fbf1563493e1486e43da49bc5868002d2bf677336ce5494a6d1fcb37935249ee', 'bae1dfda-a1f6-468a-a083-be9ebb6057ee': '0fec8438e9504eb0d410bb0f40e148bc6412120f56148bcbdbc9c702ed615884', 'd2957684-e1f2-405d-87f9-65521364f2cb': '2327bd6151115c8d63c779568a2b7a7923014a13a54e8e42bcbf832e72ff5bb5', 'd119cb74-4f99-4e9a-8ae5-b500cfbe95f3': '434746c665c5de5cccbfbfc50c53f111707836c96076377a6339401ffec5ad87', '3a669960-c05d-4bd8-ae4b-33137d486977': '4a78ac5eea1b8be60d53908421b987385a140c75876607754a1d567ce9f0a84a', '20388d1b-f4cb-40a7-b65f-686bb4e48be3': '41955640cc7eee879f9cf15c687d20e64b293491840099030faf4b54cd33005e', '5d4b8115-88b1-4952-b4b1-1a67b35d3d8e': '2ae81748cddc8254346cae41900921c662cdb717821ade042aeae70997f32295', '4d5e6282-bbb2-481c-99d4-31e581fe1737': '9429e31e3da0b0a58fbe3825d79fb85ddefead619e72d95d13847ddc66347797', '91b081d9-3044-46e9-8b0e-a9e1db7624b3': 'f0ffe8376f3f17d3ce75e1924576d1110a4c8b9df3c047dfcb8bd4b2a7c1b161', 'c85a1b9d-90dd-4958-be4a-e0fc6eaca068': 'b1f1ee6c999d338b04dc18e2ee27d8b353800e66f6b1713066ab7f33423c4c20', '9f7dfd7a-646b-4d48-86a2-684ac88398a0': '2bfdc404bc0c4b22039c4b670476e0b8bc0d1a9af69891a5716f91cd2a92866c'}


def _without_reference_layer() -> str:
    payload = json.loads((BLACKBRIAR_ROOT / "adventure.json").read_text(encoding="utf-8"))
    payload.pop("references", None)
    for encounter in payload["encounters"]:
        encounter.pop("reference_links", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(canonical).hexdigest()


def _session_one_prefix_hash() -> str:
    payload = json.loads((BLACKBRIAR_ROOT / "adventure.json").read_text(encoding="utf-8"))
    prefix = {
        "references": payload["references"][: len(SESSION_ONE_REFERENCE_IDS)],
        "reference_links": {
            encounter["id"]: encounter["reference_links"][: len(SESSION_ONE_LINKS[encounter["id"]])]
            for encounter in payload["encounters"]
        },
    }
    canonical = json.dumps(prefix, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(canonical).hexdigest()


def test_blackbriar_extraction_i_records_and_links_remain_exact_prefixes() -> None:
    adventure = load_adventure(BLACKBRIAR_ROOT / "adventure.json")
    references = adventure.reference_index()
    assert tuple(reference.id for reference in adventure.references[:10]) == SESSION_ONE_REFERENCE_IDS
    assert _session_one_prefix_hash() == "384393e014af15a85b28d0590b606f1ce60fffd7c8c857c28552b5d0bf5a0171"
    for reference_id in SESSION_ONE_REFERENCE_IDS:
        assert hashlib.sha256(references[reference_id].content.encode()).hexdigest() == SESSION_ONE_BODY_HASHES[reference_id]
    counts: Counter[str] = Counter()
    for encounter in adventure.encounters:
        prefix = SESSION_ONE_LINKS[encounter.id]
        actual = tuple(link.reference_id for link in encounter.reference_links[: len(prefix)])
        assert actual == prefix
        counts.update(actual)
    assert sum(counts.values()) == 70


def test_blackbriar_extraction_ii_records_and_links_are_bounded_and_ordered() -> None:
    adventure = load_adventure(BLACKBRIAR_ROOT / "adventure.json")
    references = adventure.reference_index()
    assert tuple(reference.id for reference in adventure.references) == REFERENCE_IDS
    assert tuple(reference.kind for reference in adventure.references) == (
        *("person",) * 12,
        *("place",) * 8,
        *("organization",) * 2,
        *("other",) * 3,
        *("object",) * 4,
    )
    assert all(UUID(reference.id).version == 4 for reference in adventure.references)
    assert references[CORIN_ID].aliases == ("Corin", "the Blackbriar page", "Pike Mill apprentice")
    assert references[HALL_ID].aliases == ("the Hall", "Judith’s house", "Blackbriar estate")
    assert references[COURT_ID].aliases == ("the Court", "Judith’s three guests", "the common welcome")
    assert references[BELL_ID].aliases == ("honest bell", "Auda Vey’s bell", "the Free Witness bell")
    counts: Counter[str] = Counter()
    for encounter in adventure.encounters:
        assert tuple(link.reference_id for link in encounter.reference_links) == EXPECTED_LINKS[encounter.id]
        for link in encounter.reference_links:
            counts[link.reference_id] += 1
            assert link.context
            assert "Blackbriar Commission" not in link.context
    assert dict(counts) == EXPECTED_COUNTS
    assert sum(counts.values()) == 185
    forbidden = (
        "Sabren Holt", "Lysa Marrin", "Toma Brack", "Neris Kade",
        "Mara is stayed", "Nell is rescued", "Judith is dead", "the feast is broken",
        "currently in custody", "currently restored", "currently severed",
    )
    for reference_id in SESSION_TWO_REFERENCE_IDS:
        reference = references[reference_id]
        text = reference.summary + "\n" + reference.content
        for phrase in forbidden:
            assert phrase not in text
        assert "remain live adventure state" not in reference.content
        assert hashlib.sha256(reference.content.encode()).hexdigest() == SESSION_TWO_BODY_HASHES[reference_id]
    assert validate_adventure(adventure).is_valid


def test_blackbriar_reference_and_voice_boundary_is_frozen() -> None:
    adventure_path = BLACKBRIAR_ROOT / "adventure.json"
    state_path = BLACKBRIAR_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)
    assert _without_reference_layer() == "a9556f50c6372c804354b69f2c0c33e5359d8a84440489daa7f955935bd5cb19"
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == "c6d81ec711c43cdce464f1156a30fe01526cf5c1ce7c578e5928e2b0ea7ce6dc"
    assert hashlib.sha256(adventure_path.read_bytes()).hexdigest() == "0520be4bef45e0d5543603b9a7f30f450ae0f09fcf3112795550fb1e159e7d61"
    assert len(adventure.encounters) == 10
    assert len(adventure.revelations) == 18
    assert len(adventure.clues) == 95
    assert len(adventure.references) == 29
    assert len(state.events) == 200
    assert validate_adventure(adventure).edge_connectivity == 4


def test_blackbriar_voice_iii_repairs_only_the_documented_seams() -> None:
    adventure_path = BLACKBRIAR_ROOT / "adventure.json"
    state_path = BLACKBRIAR_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    encounters = adventure.encounter_index()
    references = adventure.reference_index()

    expected_encounter_hashes = {'saint-orra-gallows': '9706d472595aadbda4948b463e1f489937f575c951b6dd7c91ce7a6c443a3c97', 'sedge-croft': 'dd006a25e5d61c79e99d5b7464351bd48dd34845d8ed3c543e67fba5ede6dfc3', 'saint-mercy-house': '6a5fcdfaa65df6bd938fe552a7f94f7e90c735cb2f31b83a8a3c6fe8ba9a638a', 'blackbriar-hall': '6c571524d672ea7f6887534c26142bb2ad5bee0922b28a9e0ca993770c550e6d', 'burned-refuge': 'becf6556263fcc384dc7f27e9f02d5cab293c7e10d242313001e46964256633e', 'white-pits': 'e2ff0fe511ee5350818787ff35eab4c83c60b6fc36038fde2264679ed7b3dea8', 'chapel-of-the-free-witness': 'e17fb9db1bef16a5f0dec66463116fececce3a0c9a872ef63e87e03e22c1a74d', 'moonless-mere': 'fe58e0c95bcaf916aaaa6f5f06e82957ba07392f06ceb3b892b3f322f0de6e8c', 'crow-wood': '960226f45eb3363c7487826e8f55f150cc6fa4907980484b593388acb4247ffd', 'underhall-of-the-hollow-feast': 'd854ca80cc97c800bfa949ad44044ba65bbf58cf0563d704052b222a9a7da28a'}
    expected_reference_hashes = {'fc38cc24-165f-4df6-bf04-7813911d6b8d': '7c2423998af28eeb0e992c239ced9be54deeee5f08a1a8d5ec5c1adaaa7d7d4d', '7dc115f7-e717-427c-ba9b-33f28fbd2364': '25e69824a80ec6864110c4ac84fa5f48d610a3f663775e23160569a68a2cda2c', '1ab6d356-b394-4528-b5c5-0530f8d56a65': '48e4af0db279f81c2e1a54176b6616c076647da20485073fe2503f59a416f382', '9123fa4b-e1bd-45c7-acf2-7656663ee5b3': 'abb11319ec1387790ecdaf2f0b6a9c0026397c5d554fbf5a675fe6e85774d6e6', '24f7323c-e560-49a1-8f44-95c715c2a2d0': 'e423987668f3ae60d18a6188afa1dad79df63ca1eb2b1b4fc040581cc490928e', '69daecdb-c3fe-4aab-99ad-4a9feafe9720': 'c818b59e24c53eb01a80316be3aab80986f2d251a79da05ff48527400ebd4017', 'd23d66ad-f4d2-46c3-b62d-68d7dc725cca': '06128e557d985263166f122e69d93f1a68e8c02500440824e78a03bf26376806', 'a356a5b7-8460-49ac-85ec-593b435280f7': 'e0b7580dfbdf555f056968fdd4e93b9a3171ffbbddb7aeed3cfd49a560c11490', '5af5fa39-8bd9-4dea-9c0c-f0998fd3b7a1': '88a594e0ade17664ba9af6924f9cedbd503684e049b0a35a7a0c4729636ebfa9', '03ef5b0b-c002-4f38-9a3b-47a03a379e8d': '9815cae5a628c091fc7d33a327b41f4e8f9a3b6d79a65f212ad0c34a722f724c', 'adb089a8-d281-4d33-beaa-74629823bc6a': 'e2a479c54071b31d13c4126843a7fdd70bf0ca4ee65f066184e2c63f91063cc1', 'd8e9dfa9-6c79-43e3-b8ca-e645c023469c': '745c4e154dda3f4263065c4ada997ecb4e00ecc71662dbbad78f07e799d9e71c', '426ebd86-3426-4b5a-b2ce-1b6c09b43e68': '6975e49c4193a2ccbb81ca23a3d3ccf08b2cda26baf6d4c2131f571ee09e81d0', 'b2bfc545-8e6b-446b-a961-fe60db81ffc9': 'aa0a538adc248b22b2bd23ed42a88738598582127ae3f9f9841fb86157cd3df5', '46c9f075-d08e-4251-8fba-c86f47b30411': '4447a0b01fbb6b32e0824b2c96f1956e282841e629e03470430b50187338d8f3', '9588d099-9c55-4750-b5f6-271d63b32456': '7f15b0a6b34c9c85c13c5240de4d069d8ba394d4e0426cc9d550695e135162de', 'e2455050-3963-46d2-8736-0dd826037218': '8ee8e4ddfbaf984d877c39d0e498a2e268cb804221d6947af06180d21e929f9e', '2fe9af67-c2c0-49d4-b491-a7d220b3c95e': '50b611787795f96cd214486e44ee1098360e13a9e48934d4692dba7de934253f', 'b4ac4a8e-4b89-4bd9-a9b1-4ffe2274f9eb': 'fbf1563493e1486e43da49bc5868002d2bf677336ce5494a6d1fcb37935249ee', 'bae1dfda-a1f6-468a-a083-be9ebb6057ee': '0fec8438e9504eb0d410bb0f40e148bc6412120f56148bcbdbc9c702ed615884', 'd2957684-e1f2-405d-87f9-65521364f2cb': '2327bd6151115c8d63c779568a2b7a7923014a13a54e8e42bcbf832e72ff5bb5', 'd119cb74-4f99-4e9a-8ae5-b500cfbe95f3': '434746c665c5de5cccbfbfc50c53f111707836c96076377a6339401ffec5ad87', '3a669960-c05d-4bd8-ae4b-33137d486977': '4a78ac5eea1b8be60d53908421b987385a140c75876607754a1d567ce9f0a84a', '20388d1b-f4cb-40a7-b65f-686bb4e48be3': '41955640cc7eee879f9cf15c687d20e64b293491840099030faf4b54cd33005e', '5d4b8115-88b1-4952-b4b1-1a67b35d3d8e': '2ae81748cddc8254346cae41900921c662cdb717821ade042aeae70997f32295', '4d5e6282-bbb2-481c-99d4-31e581fe1737': '9429e31e3da0b0a58fbe3825d79fb85ddefead619e72d95d13847ddc66347797', '91b081d9-3044-46e9-8b0e-a9e1db7624b3': 'f0ffe8376f3f17d3ce75e1924576d1110a4c8b9df3c047dfcb8bd4b2a7c1b161', 'c85a1b9d-90dd-4958-be4a-e0fc6eaca068': 'b1f1ee6c999d338b04dc18e2ee27d8b353800e66f6b1713066ab7f33423c4c20', '9f7dfd7a-646b-4d48-86a2-684ac88398a0': '2bfdc404bc0c4b22039c4b670476e0b8bc0d1a9af69891a5716f91cd2a92866c'}

    for encounter_id, expected_hash in expected_encounter_hashes.items():
        actual = hashlib.sha256(encounters[encounter_id].content.encode()).hexdigest()
        assert actual == expected_hash
    for reference_id, expected_hash in expected_reference_hashes.items():
        actual = hashlib.sha256(references[reference_id].content.encode()).hexdigest()
        assert actual == expected_hash

    assert sum(len(item.content.split()) for item in adventure.encounters) == 28086
    assert sum(len(item.content.split()) for item in adventure.references) == 5730
    assert sum(len(item.content.split()) for item in adventure.references[:10]) == 2172
    assert sum(len(item.content.split()) for item in adventure.references[10:]) == 3558
    assert hashlib.sha256(adventure_path.read_bytes()).hexdigest() == (
        "0520be4bef45e0d5543603b9a7f30f450ae0f09fcf3112795550fb1e159e7d61"
    )
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "c6d81ec711c43cdce464f1156a30fe01526cf5c1ce7c578e5928e2b0ea7ce6dc"
    )

    non_prose = json.loads(adventure_path.read_text(encoding="utf-8"))
    for encounter in non_prose["encounters"]:
        encounter.pop("content", None)
    for reference in non_prose["references"]:
        reference.pop("content", None)
    canonical = json.dumps(
        non_prose,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    assert hashlib.sha256(canonical).hexdigest() == (
        "10097f962bcf400f619ee383017214acd67bbba8bbe2c0a7d3c03c58293b2fe4"
    )

    expected_live_seams = {
        "sedge-croft": "The croft is both evidence room and endangered household",
        "saint-mercy-house": "Lunch is being served in the petition hall",
        "blackbriar-hall": "Petitioners wait at the front doors",
        "burned-refuge": "The west doors are still barred from outside",
        "white-pits": "The wind is turning east",
        "chapel-of-the-free-witness": "The chapel stands open because its door is gone",
        "moonless-mere": "Begin with the state actually reached",
        "crow-wood": "Start by naming what is moving now",
        "underhall-of-the-hollow-feast": "Begin by inventorying what actually reached the chamber",
    }
    for encounter_id, phrase in expected_live_seams.items():
        assert phrase in encounters[encounter_id].content

    retired_repetition = {
        "sedge-croft": "Mara Sedge is thirty-eight, a midwife",
        "saint-mercy-house": "Saint Mercy House earns Judith more loyalty than any threat",
        "blackbriar-hall": "Blackbriar Hall is a house arranged to make ownership look like administration",
        "burned-refuge": "Nineteen road travelers reached Saint Vey's granary during the famine",
        "white-pits": "During the pox year, thirty-one families paid burial fees",
        "chapel-of-the-free-witness": "The Chapel of the Free Witness was built after an older famine",
        "moonless-mere": "Moonless Mere is older than Judith",
        "crow-wood": "Crow Wood lies between the vale and Judith's three private roads",
        "underhall-of-the-hollow-feast": "The Underhall was built as Blackbriar Hall's root cellar",
    }
    for encounter_id, phrase in retired_repetition.items():
        assert phrase not in encounters[encounter_id].content

    for reference_id in SESSION_ONE_REFERENCE_IDS:
        actual = hashlib.sha256(references[reference_id].content.encode()).hexdigest()
        assert actual == SESSION_ONE_BODY_HASHES[reference_id]
    for reference_id in SESSION_TWO_REFERENCE_IDS:
        assert "remain live adventure state" not in references[reference_id].content


def test_blackbriar_reference_views_are_retrievable_and_journal_neutral() -> None:
    adventure = load_adventure(BLACKBRIAR_ROOT / "adventure.json")
    state = load_play_state(BLACKBRIAR_ROOT / "play-state.example.json")
    author_app, _ = build_authoring_app(adventure)
    status, _, library = request_wsgi(author_app, "/references")
    assert status == "200 OK"
    for title in ("Judith Crowl", "Corin Pike", "Saint Mercy House", "The Unwelcome Court", "The Honest Bell"):
        assert title in library
    status, _, detail = request_wsgi(author_app, f"/references/{UNDERHALL_ID}")
    assert status == "200 OK"
    for title in ("Saint Mercy House", "Blackbriar Hall", "The Burned Refuge", "Moonless Mere", "Crow Wood", "Underhall of the Hollow Feast"):
        assert title in detail
    play_app, project = build_play_app(adventure, state)
    before = project.snapshot
    status, _, body = request_wsgi(play_app, "/play", query=urlencode({"encounter": "underhall-of-the-hollow-feast", "reference": COURT_ID}))
    assert status == "200 OK"
    assert f'data-play-selected-reference-id="{COURT_ID}"' in body
    assert "The Unwelcome Court" in body
    assert project.snapshot == before


def test_blackbriar_packet_adds_reference_views_without_changing_demonstration() -> None:
    adventure = load_adventure(BLACKBRIAR_ROOT / "adventure.json")
    state = load_play_state(BLACKBRIAR_ROOT / "play-state.example.json")
    documents = render_adventure_documents(adventure, validate_adventure(adventure), state)
    assert len(documents) == 46
    index = documents["references/index.md"]
    for heading in ("## People", "## Places", "## Organizations", "## Objects", "## Other"):
        assert heading in index
    for reference_id in REFERENCE_IDS:
        assert f"references/{reference_id}.md" in documents
    assert_rendered_documents_match(
        documents, BLACKBRIAR_ROOT / "generated"
    )


def test_blackbriar_coherence_iii_closes_the_sequence_without_canonical_change() -> None:
    adventure_path = BLACKBRIAR_ROOT / "adventure.json"
    state_path = BLACKBRIAR_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)
    encounters = adventure.encounter_index()
    revelations = adventure.revelation_index()

    assert hashlib.sha256(adventure_path.read_bytes()).hexdigest() == (
        "0520be4bef45e0d5543603b9a7f30f450ae0f09fcf3112795550fb1e159e7d61"
    )
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "c6d81ec711c43cdce464f1156a30fe01526cf5c1ce7c578e5928e2b0ea7ce6dc"
    )
    assert len(adventure.encounters) == 10
    assert len(adventure.revelations) == 18
    assert all(revelation.required for revelation in adventure.revelations)
    assert len(adventure.clues) == 95
    assert len(adventure.references) == 29
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 185
    assert len(state.events) == 200
    assert len(state.active_events) == 200
    assert validate_adventure(adventure).edge_connectivity == 4

    non_prose = json.loads(adventure_path.read_text(encoding="utf-8"))
    for encounter in non_prose["encounters"]:
        encounter.pop("content", None)
    for reference in non_prose["references"]:
        reference.pop("content", None)
    canonical = json.dumps(
        non_prose,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    assert hashlib.sha256(canonical).hexdigest() == (
        "10097f962bcf400f619ee383017214acd67bbba8bbe2c0a7d3c03c58293b2fe4"
    )

    source_encounters: dict[str, set[str]] = {
        revelation.id: set() for revelation in adventure.revelations
    }
    for clue in adventure.clues:
        source_encounters[clue.revelation_id].add(clue.source_encounter_id)
    assert len(source_encounters) == 18
    assert {len(sources) for sources in source_encounters.values()} == {3, 4, 5, 6, 7, 8}
    for sources in source_encounters.values():
        for removed in encounters:
            assert len(sources - {removed}) >= 2

    directed_edges: dict[str, set[str]] = {
        encounter.id: set() for encounter in adventure.encounters
    }
    for clue in adventure.clues:
        target = revelations[clue.revelation_id].unlocks_encounter_id
        if target is not None and target != clue.source_encounter_id:
            directed_edges[clue.source_encounter_id].add(target)

    reached = {"saint-orra-gallows"}
    frontier = ["saint-orra-gallows"]
    while frontier:
        source = frontier.pop()
        for target in directed_edges[source] - reached:
            reached.add(target)
            frontier.append(target)
    assert reached == set(encounters)
    assert directed_edges["saint-orra-gallows"] >= {
        "sedge-croft",
        "saint-mercy-house",
        "blackbriar-hall",
        "chapel-of-the-free-witness",
        "crow-wood",
    }
    assert {
        clue.source_encounter_id
        for clue in adventure.clues
        if clue.revelation_id
        == "the-hollow-feast-will-be-completed-beneath-blackbriar-hall"
    } == {
        "blackbriar-hall",
        "burned-refuge",
        "white-pits",
        "chapel-of-the-free-witness",
        "crow-wood",
    }

    live_state_phrases = {
        "saint-orra-gallows": (
            "Mara dies only after a meaningful chance to reach her",
            "move her one body there",
            "## Leaving the green",
        ),
        "sedge-croft": (
            "The croft is both evidence room and endangered household",
            "## If the croft is reached late",
        ),
        "saint-mercy-house": (
            "a receiving place for children who cannot safely return home",
            "an accountable adult for every group leaving the house",
            "## If the house is reached late or skipped",
        ),
        "blackbriar-hall": (
            "The public stores are locked while petitioners remain outside",
            "Record separately:",
        ),
        "burned-refuge": (
            "## If the refuge is reached late",
            "freely offered hearth",
        ),
        "white-pits": (
            "Leaving one does not restore the founding pact",
            "## If the pits are reached late",
        ),
        "chapel-of-the-free-witness": (
            "## If the chapel is reached late",
            "honest bell",
        ),
        "moonless-mere": (
            "Begin with the state actually reached",
            "unborrowed reflection",
        ),
        "crow-wood": (
            "Start by naming what is moving now",
            "A failed pursuit does not make the wagon vanish",
            "## If Crow Wood is skipped or reached late",
        ),
        "underhall-of-the-hollow-feast": (
            "Begin by inventorying what actually reached the chamber",
            "A missing body, page, carrier, witness, or commander stays missing",
            "The common welcome collapses, but several private household claims remain unrepealed",
        ),
    }
    for encounter_id, phrases in live_state_phrases.items():
        for phrase in phrases:
            assert phrase in encounters[encounter_id].content

    reference_text = "\n".join(
        reference.summary + "\n" + reference.content
        for reference in adventure.references
    )
    for demonstrated_state in (
        "Mara Sedge survives under a public temporary stay",
        "All seven prosecution packets survive in three independent custody sets",
        "All seven current name vessels are covered",
        "The Guest in Ash pact is severed",
        "The Worm in White pact is narrowed but not severed",
        "The Child Behind Glass pact is severed",
        "The Mercy Book is neutralized as a feast component",
        "Judith Crowl dies after refusing surrender",
        "A temporary local council controls relief stores",
    ):
        assert demonstrated_state not in reference_text

    projection = project_play_state(adventure, state)
    consequences = "\n".join(
        consequence.text for consequence in projection.consequences
    )
    for demonstrated_state in (
        "Mara Sedge survives under a public temporary stay",
        "All seven prosecution packets survive in three independent custody sets",
        "All seven current name vessels are covered",
        "The Guest in Ash pact is severed",
        "The Worm in White pact is narrowed but not severed",
        "The Child Behind Glass pact is severed",
        "The Mercy Book is neutralized as a feast component",
        "Judith Crowl dies after refusing surrender",
        "A temporary local council controls relief stores",
    ):
        assert demonstrated_state in consequences
    assert len(projection.visits) == 10
    assert len(projection.spotted_clue_ids) == 72
    assert len(projection.corrections) == 0
    assert len(projection.consequences) == 36
    assert all(item.is_established for item in projection.revelation_progress)


    documents = render_adventure_documents(
        adventure,
        validate_adventure(adventure),
        state,
    )
    assert len(documents) == 46
    assert_rendered_documents_match(
        documents, BLACKBRIAR_ROOT / "generated"
    )


