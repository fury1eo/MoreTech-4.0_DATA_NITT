# -*- coding: utf-8 -*-
from newspaper import Article
from summarizer import Summarizer
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from selenium import webdriver
from collections import Counter
from selenium.webdriver.common.by import By
import pandas as pd
import yake
import time


class NewsFinder:
    def __init__(self, role: str, urls: list = None):
        if urls is None:
            urls = ['https://tass.ru/', 'https://ria.ru/', 'https://www.rbc.ru/', 'https://russian.rt.com/',
                    'https://lenta.ru/']
        self.role = role
        self.urls = urls
        self.role_words = ['' for i in range(len(self.role))]

    def find(self):
        """
            Первая часть. Определение ключевых слов для роли.
        """
        for i in range(len(self.role)):
            self.role_words[i] = self.role[i][:-2].lower()

        url = 'https://edunews.ru/professii/obzor/'

        driver = webdriver.Chrome()
        driver.get(url)

        XPath_links = "//p[@class='rating_professii']/span/a"

        links = driver.find_elements(By.XPATH, XPath_links)

        links_res = []

        for link in links:
            links_res.append(link.get_attribute('href'))

        proff_links_res = []

        for link in links_res:
            driver.get(link)
            xpath = "//tbody/tr/td/a"

            proff = driver.find_elements(By.XPATH, xpath)

            for r in self.role_words:
                for pr in proff:
                    if r.lower() in pr.text.lower():
                        proff_links_res.append(pr.get_attribute('href'))

        res_text = []
        for link in proff_links_res:
            article = Article(link)
            article.download()
            article.parse()

            text = article.text
            res_text.append(text)

        keywords_ = []

        for rt in res_text:
            language = "ru"
            max_ngram_size = 1
            deduplication_threshold = 0.9
            numOfKeywords = 20

            custom_kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size,
                                                        dedupLim=deduplication_threshold,
                                                        top=numOfKeywords, features=None)
            keywords = custom_kw_extractor.extract_keywords(rt)
            keywords_.append(keywords)

        numbers = []
        kwords = []

        for i in keywords_:
            for k in i:
                if k[0].isalnum():
                    numbers.append(k[-1])
                    kwords.append(k[0])

        numbers_sort = sorted(numbers)

        res_kwords = []
        for p in numbers_sort[:13]:
            res_kwords.append(kwords[numbers.index(p)])

        for r in self.role_words:
            for rk in res_kwords:
                if r in rk.lower():
                    del res_kwords[res_kwords.index(rk)]
            res_kwords.append(r)

        for i in range(len(res_kwords)):
            res_kwords[i] = res_kwords[i][:-1].lower()

        res_kwords = list(set(res_kwords))

        f = open('words_for_role.txt', 'w')
        for string in res_kwords:
            f.write(string + '\n')
        f.close()

        """
            Вторая часть. Парсинг новостей по ключевым словам.
        """
        count = 1

        words = []
        f = open('words_for_role.txt')

        for line in f:
            words.append(line[:-1])

        def parse(url):
            global count
            res = [[], []]
            driver.get(url)
            time.sleep(1)

            if 'https://russian.rt.com' in url:
                for c in range(20):
                    driver.execute_script("arguments[0].click();",
                                          driver.find_element(By.XPATH, "//div[@class='button']/a"))
                    time.sleep(1)

                links = driver.find_elements(By.CLASS_NAME, 'link_color')

                for n in range(len(links)):
                    for i in words:
                        if i in links[n].text.lower():
                            res[0].append(links[n].text)
                            res[1].append(links[n].get_attribute('href'))

            elif 'https://tass.ru' in url:
                time.sleep(3)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH,
                                                                                   '//*[@id="content_box"]/div/main/div[2]/div[2]/button'))
                time.sleep(4)
                for c in range(5):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    print(c)
                    time.sleep(1)

                text_link = driver.find_elements(By.XPATH, '//*[@class="Listing_list__qKmtM"]/a/div[1]/div/div[2]/span')
                links = driver.find_elements(By.XPATH, '//*[@class="Listing_list__qKmtM"]/a')

                for n in range(len(text_link)):
                    for i in words:
                        if i in text_link[n].text.lower():
                            res[0].append(text_link[n].text)
                            res[1].append(links[n].get_attribute('href'))

            elif 'https://lenta.ru' in url:
                for c in range(5):
                    currentUrl = f'{url}{c}/'
                    time.sleep(1)

                    driver.get(currentUrl)
                    text_link = driver.find_elements(By.TAG_NAME, 'h3')
                    links = driver.find_elements(By.XPATH, "//*[@id='body']/div[3]/div[3]/main/div/section/ul/li")

                    for n in range(len(text_link)):
                        for i in words:
                            if i in text_link[n].text.lower():
                                res[0].append(text_link[n].text)
                                res[1].append(links[n].find_element(By.TAG_NAME, 'a').get_attribute('href'))

            elif 'https://ria.ru' in url:
                for c in range(5):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)

                driver.execute_script("window.scrollTo(0, 0);")

                text_link = driver.find_elements(By.CLASS_NAME, 'list-item__title')

                for n in range(len(text_link)):
                    for i in words:
                        if i in text_link[n].text.lower():
                            res[0].append(text_link[n].text)
                            res[1].append(text_link[n].get_attribute('href'))

            elif 'https://www.rbc.ru' in url:
                for c in range(5):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)

                text_link = driver.find_elements(By.CLASS_NAME, 'item__title')
                links = driver.find_elements(By.CLASS_NAME, 'item__link')

                for n in range(len(text_link)):
                    for i in words:
                        if i in text_link[n].text.lower():
                            res[0].append(text_link[n].text)
                            res[1].append(links[n].get_attribute('href'))

            df_ = pd.DataFrame(data=res, index=['text', 'link'])
            df = df_.T

            df = df.drop_duplicates(subset=['text'], keep='first')
            with pd.ExcelWriter(f'pars_sites_{count}_pred.xlsx') as writer:
                df.to_excel(writer)
            count += 1

        driver = webdriver.Chrome()

        for url in self.urls:
            parse(url)

        """ Объединение всех таблиц в одну """
        table = [[], []]
        for i in range(1, len(self.urls) + 1):
            tableTitles = list(pd.read_excel(f'pars_sites_{i}')['text'])
            tableLinks = list(pd.read_excel(f'pars_sites_{i}')['link'])
            table[0].append(tableTitles)
            table[1].append(tableLinks)

        dataFrame = pd.DataFrame(data=table, index=['text', 'link'])
        dataFrame = dataFrame.T

        dataFrame = dataFrame.drop_duplicates(subset=['text'], keep='first')
        with pd.ExcelWriter(f'pars_sites_table.xlsx') as writer:
            dataFrame.to_excel(writer)

        """
            Третья часть. Поиск сути новостей.
            (Этот процесс довольно трудоемкий)
        """
        start = time.time()
        print('Таймер запущен')

        TABLE_NAME = 'pars_sites_table.xlsx'
        words = []
        f = open('words_for_role.txt')
        for i in f:
            words.append(i[:-1])

        words = ' '.join(words)

        links = list(pd.read_excel(TABLE_NAME)['link'])

        summary = [words]
        ind_summary = []
        result_summary = []

        def Result_summary(frequency_list):
            global ind_summary, result_summary
            frequency_list_sort = sorted(frequency_list, reverse=True)
            ind_summary = [(frequency_list.index(frequency_list_sort[0])),
                           (frequency_list.index(frequency_list_sort[1])),
                           (frequency_list.index(frequency_list_sort[2]))]
            result_summary = [summary[ind_summary[0] + 1], summary[ind_summary[1] + 1], summary[ind_summary[2] + 1]]
            return result_summary

        for url in links:
            try:
                article = Article(url, language='ru')
                article.download()
                article.parse()

                text = article.text

                bert_model = Summarizer()
                bert_summary = ''.join(bert_model(text, min_length=40))
                summary.append(bert_summary)
                print(f'Прошло времени: {time.time() - start}')
            except:
                summary.append('--')
                continue

        model = SentenceTransformer('bert-base-nli-mean-tokens')
        sentence_embeddings = model.encode(summary)
        sentence_embeddings.shape

        frequency_list = (cosine_similarity(
            [sentence_embeddings[0]],
            sentence_embeddings[1:]
        ))[0].tolist()

        Result_summary(frequency_list)

        df_all_sum = pd.DataFrame(data=[links, summary[1:]], index=['links', 'summary']).T
        with pd.ExcelWriter('roleTable_all_summ.xlsx') as writer:
            df_all_sum.to_excel(writer)

        df_top_sum = pd.DataFrame(
            data=[[links[ind_summary[0]], links[ind_summary[1]], links[ind_summary[2]]], result_summary],
            index=['links', 'summary']).T
        with pd.ExcelWriter('roleTable_top_summ.xlsx') as writer:
            df_top_sum.to_excel(writer)

        print(f'Прошло времени: {time.time() - start}')

        """
            Четвертая часть. Поиск тренда.
        """
        df = pd.read_excel('roleTable_all_summ.xlsx')
        summary = list(df['summary'])

        all_words = []

        def Result_summary2(frequency_list):
            global ind_summary, result_summary
            frequency_list_sort = sorted(frequency_list, reverse=True)
            ind_summary = [(frequency_list.index(frequency_list_sort[0]))]
            result_summary = [summary[ind_summary[0] + 1]]
            return result_summary

        for text in summary:
            language = "ru"
            max_ngram_size = 1
            deduplication_threshold = 0.1
            numOfKeywords = 3

            custom_kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size,
                                                        dedupLim=deduplication_threshold,
                                                        top=numOfKeywords, features=None)
            keywords = custom_kw_extractor.extract_keywords(text.lower())
            for i in keywords:
                if i[0].isalnum():
                    all_words.append(i[0].lower())

        c = Counter(all_words)
        top_3 = c.most_common(7)
        top3_res = []
        for i in top_3:
            top3_res.append(i[0].lower())

        sentence_sum = [' '.join(top3_res)]

        for text in summary:
            sentence_sum.append(text.lower())

        model = SentenceTransformer('bert-base-nli-mean-tokens')
        sentence_embeddings = model.encode(sentence_sum)
        sentence_embeddings.shape

        frequency_list = (cosine_similarity(
            [sentence_embeddings[0]],
            sentence_embeddings[1:]
        ))[0].tolist()

        top1_text = Result_summary2(frequency_list)
        tr = top1_text[0].split('\n')
        result = [tr[0]]

        f = open('trend.txt', 'w')
        for string in result:
            f.write(string + '\n')
        f.close()

        """
            Пятая часть. Поиск инсайтов.
        """
        df = pd.read_excel('roleTable_all_summ.xlsx')
        summary = list(df['summary'])

        f = open('trend.txt')
        for i in f:
            trend = i

        words = [' '.join([k.lower() for k in trend.split(' ')])]

        sentence_sum = words + summary

        model = SentenceTransformer('bert-base-nli-mean-tokens')
        sentence_embeddings = model.encode(sentence_sum)
        sentence_embeddings.shape

        frequency_list = (cosine_similarity(
            [sentence_embeddings[0]],
            sentence_embeddings[1:]
        ))[0].tolist()

        top3_text = Result_summary(frequency_list)

        result = []
        for i in range(3):
            tr = top3_text[i].split('\n')
            tr_res = tr[0]
            result.append(tr_res)

        f = open('insights.txt', 'w')
        for string in result:
            f.write(string + '\n')
        f.close()

        """ Объединение данных в одну таблицу """
        fTrend_ = open('trend.txt')
        fTrend = [i for i in fTrend_]
        fInsight_ = open('insights.txt')
        fInsight = [i for i in fInsight_]

        dataFrameTop_link = list(pd.read_excel('roleTable_all_summ.xlsx')['links'])
        dataFrameTop_title = list(pd.read_excel('roleTable_all_summ.xlsx')['summary'])

        currentTable = pd.DataFrame(data=[dataFrameTop_title, dataFrameTop_link, fTrend, fInsight],
                                    index=['title', 'link', 'trend', 'insight']).T
        with pd.ExcelWriter('news_table.xlsx') as writer:
            currentTable.to_excel(writer)
