from datetime import datetime, timedelta
from flask import render_template, jsonify, request, flash
from forms import CPFCNPJForm
from database_manager import DatabaseManager
import requests

class CPFCNPJApp:
    def __init__(self):
        self.form = CPFCNPJForm()
        self.db_manager = DatabaseManager()

    def consultar_api(self, cpfcnpj):
        API_URL_PF = "https://plataforma.bigdatacorp.com.br/pessoas"
        API_URL_PJ = "https://plataforma.bigdatacorp.com.br/empresas"
        HEADERS = {
            "accept": "application/json",
            "content-type": "application/json",
            "AccessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiR0FCUklFTC5QQVpAU0lDT09CLkNPTS5CUiIsImp0aSI6ImM3NTIxZTMzLTE0MTMtNDcwMy04OTk0LTJjODE3ZTQxNjA3ZSIsIm5hbWVVc2VyIjoiR2FicmllbCBNYXJ0aW5zIFBheiIsInVuaXF1ZV9uYW1lIjoiR0FCUklFTC5QQVpAU0lDT09CLkNPTS5CUiIsImRvbWFpbiI6IlNJQ09PQiBVTklDRU5UUk8gQlIiLCJwcm9kdWN0cyI6WyJCSUdCT09TVCIsIkJJR0lEIl0sIm5iZiI6MTcxODM2NDc3NCwiZXhwIjoxNzQ5OTAwNzc0LCJpYXQiOjE3MTgzNjQ3NzQsImlzcyI6IkJpZyBEYXRhIENvcnAuIn0.G8JqjvQDYS2iOWvYhDtuoZPaAC52lNN2QxUXf5ZOMk4",
            "TokenId": "666c2a66434fddec816f5680"
        }

        if len(cpfcnpj) == 11:
            api_url = API_URL_PF
            payload = {
                "q": f"doc{{{cpfcnpj}}}",
                "Datasets": (
                    "basic_data {Name, Gender, Age, MotherName, FatherName}, "
                    "university_student_data {ScholarshipHistory, PublicationHistory, NumberOfUndergraduateCourses}, "
                    "occupation_data{TotalProfessions,TotalActiveProfessions,TotalIncome, TotalIncomeRange, TotalDiscounts, IsEmployed}, "
                    "financial_interests{FinancialActivityLevel, IsFinancialSectorOwner, IsFinancialSectorEmployee, RelatedFinancialInstitutionActivities ,PossibleUtilizedBanks}, "
                    "professional_turnover{IsCurrentlyEmployed, IsEntrepeneur, HasWorkedInPrivateSector, HasWorkedInPublicSector}, "
                    "lawsuits_distribution_data{TotalLawsuits, Distribuição dos tipos de processos,CourtNameDistribution,StateDistribution}, "
                    "collections{IsCurrentlyOnCollection}, "
                    "indebtedness_question{LikelyInDebt}"
                )
            }
        else:
            api_url = API_URL_PJ
            payload = {
                "q": f"doc{{{cpfcnpj}}}",
                "Datasets": (
                    "registration_data, "
                    "collections{IsCurrentlyOnCollection, TotalCollectionOccurrences, TotalCollectionOrigins, CurrentConsecutiveCollectionMonths, MaxConsecutiveCollectionMonths}, "
                    "OwnersLawsuitsDistributionData{TotalOwners,MaxLawsuitsPerOwner,TypeDistribution, StatusDistribution, CourtNameDistribution, CourtTypeDistribution}, "
                    "LawsuitsDistributionData{TotalLawsuits, TypeDistribution},"
                    "company_group_rfcontact{TotalCompanies, TotalIncomeRange, TotalEmployeesRange}, "
                    "government_debtors{TotalDebtValue, TotalDebts}"
                )
            }

        try:
            response = requests.post(api_url, json=payload, headers=HEADERS)
            if response.status_code == 200:
                data = response.json()
                if "Result" in data:
                    return data["Result"]
                else:
                    print(f"No 'Result' found for CPF/CNPJ {cpfcnpj}")
                    print(f"Response Data: {data}")
            else:
                print(f"Failed to retrieve data for CPF/CNPJ {cpfcnpj}: {response.status_code}, {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

        return None

    def index(self):
        if self.form.validate_on_submit():
            cpfcnpj = self.form.cpfcnpj.data.strip()
            record = self.db_manager.get_data(cpfcnpj)
            if record:
                if 'data' in record and record['last_updated'] > datetime.now() - timedelta(days=30):
                    data = record['data']
                else:
                    data = self.consultar_api(cpfcnpj)
                    if data:
                        self.db_manager.store_data(cpfcnpj, data)
                if data:
                    return jsonify(data)
                else:
                    flash('Erro ao consultar CPF/CNPJ. Por favor, tente novamente.', 'danger')
            else:
                data = self.consultar_api(cpfcnpj)
                if data:
                    self.db_manager.store_data(cpfcnpj, data)
                    return jsonify(data)
                else:
                    flash('Erro ao consultar CPF/CNPJ. Por favor, tente novamente.', 'danger')

        if request.method == 'POST' and not self.form.validate_on_submit():
            response = jsonify({'errors': self.form.errors})
            response.status_code = 400
            return response

        return render_template('index.html', form=self.form)
