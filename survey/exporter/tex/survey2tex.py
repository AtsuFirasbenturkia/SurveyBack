# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import logging
import os

from django.conf import settings
from future import standard_library

from survey.exporter.survey2x import Survey2X
from survey.exporter.tex.latex_file import LatexFile
from survey.exporter.tex.question2tex import Question2Tex
from survey.exporter.tex.question2tex_chart import Question2TexChart
from survey.exporter.tex.question2tex_raw import Question2TexRaw
from survey.exporter.tex.question2tex_sankey import Question2TexSankey

standard_library.install_aliases()


LOGGER = logging.getLogger(__name__)


class Survey2Tex(Survey2X):

    ANALYSIS_FUNCTION = []

    def __init__(self, survey, configuration=None):
        Survey2X.__init__(self, survey)
        self.tconf = configuration

    def _synthesis(self, survey):
        """ Return a String of a synthesis of the report. """
        pass

    def _additional_analysis(self, survey, latex_file):
        """ Perform additional analysis. """
        for function_ in self.ANALYSIS_FUNCTION:
            LOGGER.info("Performing additional analysis with %s", function_)
            latex_file.text += function_(survey)

    def treat_question(self, question, survey):
        LOGGER.info("Treating, %s %s", question.pk, question.text)
        options = self.tconf.get(survey_name=self.survey.name,
                                 question_text=question.text)
        multiple_charts = options.get("multiple_charts")
        if not multiple_charts:
            multiple_charts = {"": options.get("chart")}
        question_synthesis = ""
        i = 0
        for chart_title, opts in multiple_charts.items():
            i += 1
            if chart_title:
                # "" is False, by default we do not add section or anything
                mct = options["multiple_chart_type"]
                question_synthesis += "\%s{%s}" % (mct, chart_title)
            tex_type = opts.get("type")
            if tex_type == "raw":
                q2tex = Question2TexRaw(question, **opts)
            elif tex_type == "sankey":
                q2tex = Question2TexSankey(question)
            else:
                q2tex = Question2TexChart(question, latex_label=i, **opts)
            question_synthesis += q2tex.tex()
        section_title = Question2Tex.html2latex(question.text)
        return u"""
\\clearpage{}
\\section{%s}

\label{sec:%s}

%s

""" % (section_title, question.pk, question_synthesis)

    def generate(self, path, output=None):
        """ Compile the pdf from the tex file. """
        dir_name, file_name = os.path.split(path)
        os.chdir(dir_name)
        os.system("pdflatex {}".format(file_name))
        os.system("pdflatex {}".format(file_name))
        if output is not None:
            os.system("mv {}.pdf {}".format(file_name[:-3], output))
        os.chdir(settings.ROOT)

    def survey_to_x(self):
        document_class = self.tconf.get("document_class",
                                        survey_name=self.survey.name)
        kwargs = self.tconf.get(survey_name=self.survey.name)
        del kwargs["document_class"]
        ltxf = LatexFile(document_class, **kwargs)
        self._synthesis(self.survey)
        for question in self.survey.questions.all():
            ltxf.text += self.treat_question(question, self.survey)
        self._additional_analysis(self.survey, ltxf)
        return ltxf.document

    def generate_pdf(self):
        """ Compile the pdf from the tex file. """
        self.generate_file()
        self.generate(self.file_name())