import psycopg2
import pandas as pd
import os
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Image,PageBreak,TableStyle
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
from reportlab.lib import colors

def callDatabase(query, dbname, user, password, host, port):
    try:
        connection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        cursor = connection.cursor()
        cursor.execute(query)

        # Get column names
        column_names = [desc[0] for desc in cursor.description]

        # Fetch data and turn it into a DataFrame 
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=column_names)

        print('Executed successfully')
        cursor.close()
        connection.commit()
        connection.close()

        return df  # Return the DataFrame

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)
        return None  # Return None on error

def makestatement(gendconf=None, ageConf=None, dbname=None, user=None, password=None, host=None, port=None):
    statementGender = """
    select
        sum(case when genderpredicted = 'M' then 1 else 0 end) as "Male", 
        sum(case when genderpredicted = 'F' then 1 else 0 end) as "Female", 
        count(genderpredicted) as "total" 
        from genderprediction
    """
    
    statementAge = """
    select
        sum(case when agepredicted = '6~13' then 1 else 0 end) as "6~13", 
        sum(case when agepredicted = '14~19' then 1 else 0 end) as "14~19", 
        sum(case when agepredicted = '20~32' then 1 else 0 end) as "20~32", 
        sum(case when agepredicted = '33~45' then 1 else 0 end) as "33~45", 
        sum(case when agepredicted = '46~60' then 1 else 0 end) as "46~60", 
        sum(case when agepredicted = '60+' then 1 else 0 end) as "60+", 
        count(agepredicted) as "total" 
        from ageprediction
    """
    
    statementBoth1 =  """
    select
            sum(case when agepredicted = '6~13' then 1 else 0 end) as "6~13", 
            sum(case when agepredicted = '14~19' then 1 else 0 end) as "14~19", 
            sum(case when agepredicted = '20~32' then 1 else 0 end) as "20~32", 
            sum(case when agepredicted = '33~45' then 1 else 0 end) as "33~45", 
            sum(case when agepredicted = '46~60' then 1 else 0 end) as "46~60", 
            sum(case when agepredicted = '60+' then 1 else 0 end) as "60+"
        from genderprediction G inner join agePrediction A on G.faceId=a.FaceId 
        where g.genderpredicted = 'F'       
    """

    statementBoth2 =  """
    select
            sum(case when agepredicted = '6~13' then 1 else 0 end) as "6~13", 
            sum(case when agepredicted = '14~19' then 1 else 0 end) as "14~19", 
            sum(case when agepredicted = '20~32' then 1 else 0 end) as "20~32", 
            sum(case when agepredicted = '33~45' then 1 else 0 end) as "33~45", 
            sum(case when agepredicted = '46~60' then 1 else 0 end) as "46~60", 
            sum(case when agepredicted = '60+' then 1 else 0 end) as "60+"
        from genderprediction G inner join agePrediction A on G.faceId=a.FaceId 
        where g.genderpredicted = 'M'       
    """

    if gendconf and ageConf:
        statementGender += f' Where confidence >= {gendconf}'
        statementBoth1 += f' And g.confidence >= {gendconf} AND a.confidence >= {ageConf}'
        statementBoth2 += f' And g.confidence >= {gendconf} AND a.confidence >= {ageConf}'
        statementAge += f' Where confidence >= {ageConf}'

    elif gendconf:
        statementGender += f' Where confidence >= {gendconf}'
        statementBoth1 += f' And g.confidence >= {gendconf}'
        statementBoth2 += f' And g.confidence >= {gendconf}'

    elif ageConf:
        statementAge += f' Where confidence >= {ageConf}'
        statementBoth1 += f' And g.confidence >= {ageConf}'
        statementBoth2 += f' And g.confidence >= {ageConf}'

    genDF = callDatabase(statementGender, dbname, user, password, host, port)
    gendata = genDF.to_dict(orient='records')[0]
    genDF = pd.DataFrame({'Gender': list(gendata.keys()), 'Count': list(gendata.values())})
    
    ageDF = callDatabase(statementAge, dbname, user, password, host, port)
    Agedata = ageDF.to_dict(orient='records')[0]
    ageDF = pd.DataFrame({'Ages': list(Agedata.keys()), 'Count': list(Agedata.values())})
    
    bothDF1 = callDatabase(statementBoth1, dbname, user, password, host, port)
    bothdata1 = bothDF1.to_dict(orient='records')[0]
    bothDF1 = pd.DataFrame({'Gender': ['Female' for i in range(6)],'Age': list(bothdata1.keys()), 'Count': list(bothdata1.values())})

    bothDF2 = callDatabase(statementBoth2, dbname, user, password, host, port)
    bothdata2 = bothDF2.to_dict(orient='records')[0]
    bothDF2 = pd.DataFrame({'Gender': ['Male' for i in range(6)],'Age': list(bothdata2.keys()), 'Count': list(bothdata2.values())})

    return genDF, ageDF, bothDF1,bothDF2

def style_table(table):
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]

    # Apply the style to the table
    table.setStyle(TableStyle(style))


def generate_report(gendconf=None, ageConf=None, filename=None, dbname='mydb', user='username', password='1234', host='localhost', port='5432'):
    genDF, ageDF, bothDF1, bothDF2 = makestatement(gendconf, ageConf, dbname, user, password, host, port)

    if filename is None:
        doc = SimpleDocTemplate("database_report.pdf")
    else:
        doc = SimpleDocTemplate(f"{filename}.pdf")
    elements = []

    # Add Title
    elements.append(Paragraph("Age and Gender Report", getSampleStyleSheet()["Title"]))

    # Add Gender DataFrame as Table
    if genDF is not None:
        elements.append(Paragraph("Gender Distribution:", getSampleStyleSheet()["Heading3"]))
        data = [genDF.columns.tolist()] + genDF.values.tolist()
        gen_table = Table(data, colWidths=100, rowHeights=30)
        style_table(gen_table)
        elements.append(gen_table)
        
        counts = genDF['Count'].tolist()[:-1]

        plt.figure(figsize=(8, 6))
        wedges, texts, autotexts = plt.pie(counts, labels=['Male','Female'],
                                           autopct='%1.1f%%', startangle=140,)
        plt.gca().add_artist(plt.Circle((0, 0), 0.35, color='white'))
        plt.title('Gender Distribution')
        
        total = sum(counts)
        for i, count in enumerate(counts):
            percentage = 100 * count / total
            autotext = autotexts[i]
            autotext.set_text(f'{percentage:.1f}%\n{count}')
            autotext.set_position((autotext.get_position()[0], autotext.get_position()[1] - 0.1))
        
        plt.savefig('gender_distribution.png')
    
        elements.append(Paragraph("Gender Distribution Chart:", getSampleStyleSheet()["Heading3"]))
        elements.append(Image('gender_distribution.png', width=600, height=450))
        elements.append(PageBreak())

    
    if ageDF is not None:
        elements.append(Paragraph("Age Distribution:", getSampleStyleSheet()["Heading3"]))
        data = [ageDF.columns.tolist()] + ageDF.values.tolist()
        age_table = Table(data, colWidths=100, rowHeights=30)
        style_table(age_table)
        elements.append(age_table)

        plt.figure(figsize=(8, 6))
        ageDF[:-1].plot(kind='bar', legend=None)
        plt.title('Age Distribution')
        plt.xlabel('Age')
        plt.ylabel('Count')
        new_xtick_labels = ['6~13','14~19', '20~32', '33~45', '46~60', '60+']
        plt.xticks(range(len(new_xtick_labels)), new_xtick_labels, rotation=45)
    
        plt.savefig('age_distribution.png')
        elements.append(Paragraph("Age Distribution Plot:", getSampleStyleSheet()["Heading3"]))
        elements.append(Image('age_distribution.png', width=500, height=350))
        elements.append(PageBreak())

    # Add Both DataFrame as Table
    if bothDF1 is not None and bothDF2 is not None:
        elements.append(Paragraph("Gender and Age Distribution:", getSampleStyleSheet()["Heading3"]))
        bothDF = pd.concat([bothDF1, bothDF2], axis=0)
        data = [bothDF.columns.tolist()] + bothDF.values.tolist()
        both_table = Table(data, colWidths=100, rowHeights=30)
        style_table(both_table)
        elements.append(both_table)
        elements.append(PageBreak())

        plt.figure(figsize=(10, 6))
        try:
            plt.bar(bothDF1['Age'], bothDF1['Count'])
            plt.title('Count of Each Age Group In Female')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
            plt.savefig('female_age_distribution.png')

            plt.bar(bothDF2['Age'], bothDF2['Count'])
            plt.title('Count of Each Age Group In Male')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
            plt.savefig('male_age_distribution.png')
            
            elements.append(Paragraph("Gender and Age Distribution Plot:", getSampleStyleSheet()["Heading3"]))
            elements.append(Image('female_age_distribution.png', width=500, height=300))
            elements.append(Image('male_age_distribution.png', width=500, height=300))
            elements.append(PageBreak())
        except KeyError as e:
            print("Error occurred while generating plots:", e)

    # Build and save the PDF
    doc.build(elements)
    print("Report generated successfully")
    os.remove('age_distribution.png')
    os.remove('male_age_distribution.png')
    os.remove('female_age_distribution.png')
    os.remove('gender_distribution.png')
