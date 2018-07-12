

import os
import yaml
import random
import uuid
import sys
import traceback
import argparse
from tqdm import tqdm
from collections import Counter

from .questions import question_forms
from .generate_graph import GraphGenerator
from .types import *

import logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('--count', type=int, default=10000, help="Number of (G,Q,A) to generate")
	parser.add_argument('--log-level', type=str, default='INFO')
	parser.add_argument('--questions-per-graph', type=int, default=1, help="Number of (Q,A) per G")
	parser.add_argument('--quick', action='store_true', help="Generate small graphs (faster)")
	parser.add_argument('--omit-graph', action='store_true', help="Don't export the graph")
	parser.add_argument('--int-names', action='store_true', help="Use integers as names")
	parser.add_argument('--only-type', type=str, default=None, help="Only generate questions of type prefix")


	FLAGS = parser.parse_args()

	logging.basicConfig()
	logger.setLevel(FLAGS.log_level)
	logging.getLogger('gqa').setLevel(FLAGS.log_level)

	filename = f"./data/gqa-{uuid.uuid4()}.yaml"
	logger.info(f"Generating {FLAGS.count} (G,Q,A) tuples into {filename}")

	os.makedirs("./data", exist_ok=True)

	with open(filename, "w") as file:

		f_try = Counter()
		f_success = Counter()

		def forms():
			while True:
				for form in question_forms:
					yield form

		def specs():
			form_gen = forms()
			i = 0
			with tqdm(total=FLAGS.count) as pbar:
				while i < FLAGS.count:

					try:
						logger.debug("Generating graph")
						g = GraphGenerator(small=FLAGS.quick,int_names=FLAGS.int_names).generate().graph_spec

						if len(g.nodes) == 0 or len(g.edges) == 0:
							raise ValueError("Empty graph was generated")


						j = 0
						while j < FLAGS.questions_per_graph:
						
							form = next(form_gen)

							if FLAGS.only_type is None or FLAGS.only_type == form.type_string[:len(FLAGS.only_type)]:

								f_try[form.type_string] += 1
								
								logger.debug(f"Generating question '{form.english}'")
								q, a = form.generate(g)

								f_success[form.type_string] += 1
								i += 1
								j += 1
								pbar.update(1)

								logger.debug(f"Question: '{q}', answer: '{a}'")

								if FLAGS.omit_graph:
									yield DocumentSpec(None,q,a).stripped()
								else:
									yield DocumentSpec(g,q,a).stripped()
							
					except Exception as ex:
						# print(traceback.format_exception(None, # <- type(e) by docs, but ignored
						# 	ex, ex.__traceback__),
						# 	file=sys.stderr, flush=True)
						logger.debug(f"Exception {ex} whilst trying to generate GQA")
						# Continue to next attempt
						

		yaml.dump_all(specs(), file, explicit_start=True)

		logger.info(f"GQA per question type: {f_success}")

		for i in f_try:
			if i in f_success: 
				if f_success[i] < f_try[i]:
					logger.warn(f"Question form {i} failed to generate {f_try[i] - f_success[i]}/{f_try[i]}")
			else:
				logger.warn(f"Question form {i} totally failed to generate")

				



