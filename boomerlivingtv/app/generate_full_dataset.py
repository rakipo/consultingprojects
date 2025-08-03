#!/usr/bin/env python3
"""
Generate full dataset of 100 sample publications for PostgreSQL
"""

import psycopg2
import json
from datetime import datetime, date
import random

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'movies',
    'user': 'postgres',
    'password': 'password123'
}

# Authors and their specializations
AUTHORS = [
    ('Dr. Sarah Chen', 'Healthcare', 12),
    ('Michael Rodriguez', 'Financial', 10),
    ('Dr. Alex Thompson', 'Technology', 15),
    ('Dr. Emily Watson', 'Healthcare', 8),
    ('Dr. James Wilson', 'Sustainability', 9),
    ('Lisa Chang', 'Lifestyle', 11),
    ('Dr. Robert Kim', 'Education', 7),
    ('Dr. Maria Santos', 'Sustainability', 6),
    ('Jennifer Lee', 'Technology', 8),
    ('David Park', 'Technology', 14)
]

# Domains and their tags
DOMAINS = {
    'Healthcare': ['Healthcare', 'AI', 'Technology'],
    'Financial': ['Fintech', 'Financial', 'Technology'],
    'Technology': ['AI', 'Technology'],
    'Sustainability': ['Sustainability', 'Weather'],
    'Lifestyle': ['Lifestyle', 'Healthcare'],
    'Education': ['Education', 'Technology']
}

# Sample titles and content templates
TITLE_TEMPLATES = {
    'Healthcare': [
        'AI-Powered Medical Diagnosis Revolution',
        'Telemedicine Adoption Accelerates Post-Pandemic',
        'Precision Medicine Tailoring Treatment',
        'Digital Health Records Transform Care',
        'Robotic Surgery Advances Patient Outcomes'
    ],
    'Financial': [
        'Blockchain Technology Revolutionizes Banking',
        'Digital Payment Systems Drive Inclusion',
        'Cryptocurrency Adoption in Mainstream Finance',
        'Robo-Advisors Democratize Investment Management',
        'RegTech Solutions Streamline Compliance'
    ],
    'Technology': [
        'Machine Learning Advances Enable Breakthroughs',
        'Neural Network Architectures Evolve',
        'Quantum Computing Promises Revolutionary Solutions',
        'Edge Computing Brings Processing Closer',
        'Cybersecurity Trends Address Evolving Threats'
    ],
    'Sustainability': [
        'Renewable Energy Solutions Accelerate Decarbonization',
        'Climate Change Research Reveals Impacts',
        'Circular Economy Principles Transform Waste',
        'Carbon Capture Technologies Offer Mitigation',
        'Sustainable Agriculture Practices Protect Environment'
    ],
    'Lifestyle': [
        'Wellness Trends Focus on Holistic Health',
        'Digital Wellness Practices Address Overuse',
        'Mindfulness and Meditation Gain Validation',
        'Fitness Technology Revolutionizes Monitoring',
        'Work-Life Balance Strategies Adapt'
    ],
    'Education': [
        'Online Learning Evolution Transforms Accessibility',
        'AI-Powered Tutoring Systems Provide Support',
        'Digital Literacy Education Prepares Students',
        'STEM Education Innovation Prepares Careers',
        'Inclusive Education Practices Ensure Opportunities'
    ]
}

def generate_content(domain, title):
    """Generate sample content for an article"""
    content_templates = {
        'Healthcare': "Healthcare technology is transforming patient care through innovative solutions and digital transformation. Medical professionals are adopting new tools to improve diagnosis accuracy and treatment outcomes. Patient engagement has increased through digital health platforms and telemedicine services. Healthcare systems are investing in infrastructure to support these technological advances. The integration of AI and machine learning is revolutionizing medical research and clinical practice. Data privacy and security remain critical considerations in healthcare technology implementation. Regulatory frameworks are evolving to ensure safe and effective use of new technologies. Healthcare providers are training staff to effectively utilize these new technological capabilities. The future of healthcare will be increasingly digital and personalized for individual patient needs. Cost-effectiveness and accessibility are driving factors in healthcare technology adoption worldwide.",
        'Financial': "Financial technology is revolutionizing how people and businesses manage money and conduct transactions. Digital payment systems are making financial services more accessible to underserved populations globally. Blockchain technology provides secure and transparent methods for recording financial transactions and agreements. Artificial intelligence is being used to detect fraud and assess credit risk more accurately. Regulatory compliance is becoming more efficient through automated reporting and monitoring systems. Investment management is being democratized through robo-advisors and low-cost digital platforms. Cryptocurrency and digital assets are gaining acceptance as legitimate investment and payment options. Financial institutions are partnering with fintech companies to innovate and improve customer experiences. Data analytics provides insights into customer behavior and preferences for personalized financial services. The future of finance will be increasingly digital, automated, and customer-centric in its approach.",
        'Technology': "Technology continues to advance at an unprecedented pace, transforming industries and daily life experiences. Artificial intelligence and machine learning are becoming integral parts of business operations and decision-making processes. Cloud computing provides scalable and flexible infrastructure for organizations of all sizes worldwide. Cybersecurity measures are evolving to address increasingly sophisticated threats and attack vectors. Internet of Things devices are creating interconnected ecosystems that generate valuable data insights. Mobile technology enables remote work and global collaboration across different time zones and locations. Automation is streamlining repetitive tasks and allowing humans to focus on more creative work. Data analytics and visualization tools help organizations make informed decisions based on evidence. The digital transformation is accelerating across all sectors, requiring new skills and approaches. Future technology developments will focus on sustainability, accessibility, and human-centered design principles.",
        'Sustainability': "Sustainability initiatives are becoming critical for addressing climate change and environmental degradation challenges. Renewable energy sources are becoming more cost-effective and efficient than traditional fossil fuels. Circular economy principles are being adopted to reduce waste and maximize resource utilization. Carbon capture and storage technologies offer potential solutions for reducing atmospheric greenhouse gases. Sustainable agriculture practices help protect biodiversity while maintaining food security for growing populations. Green building standards are being implemented to reduce energy consumption and environmental impact. Transportation systems are transitioning to electric and alternative fuel vehicles to reduce emissions. Water conservation and management strategies are essential for addressing scarcity in many regions. Corporate sustainability reporting is becoming mandatory in many jurisdictions to ensure accountability. The future requires coordinated global action to achieve sustainability goals and protect the planet.",
        'Lifestyle': "Lifestyle trends are evolving to prioritize health, wellness, and work-life balance in modern society. Digital wellness practices help people manage technology use and maintain healthy relationships with devices. Mindfulness and meditation are gaining scientific validation for their mental and physical health benefits. Fitness technology provides personalized insights and motivation for maintaining active and healthy lifestyles. Nutrition science is advancing understanding of how diet affects overall health and disease prevention. Sleep optimization is receiving increased attention as research reveals its critical importance for wellbeing. Social connections and community engagement are recognized as essential components of mental health. Sustainable living practices are being adopted to reduce environmental impact and promote conscious consumption. Work flexibility and remote options are becoming standard expectations for maintaining life balance. The future of lifestyle will emphasize prevention, personalization, and holistic approaches to human flourishing.",
        'Education': "Education is undergoing digital transformation to meet the needs of 21st-century learners and society. Online learning platforms provide flexible and accessible education opportunities for diverse student populations. Artificial intelligence is personalizing learning experiences and providing adaptive feedback to individual students. Virtual and augmented reality technologies create immersive educational experiences for complex subjects. Collaborative tools enable global classroom connections and cross-cultural learning opportunities for students. Assessment methods are evolving to measure critical thinking and problem-solving skills beyond memorization. Teacher training programs are incorporating technology integration and digital pedagogy best practices. Inclusive education practices ensure equal opportunities for students with diverse abilities and backgrounds. Lifelong learning is becoming essential as rapid technological change requires continuous skill development. The future of education will be more personalized, flexible, and focused on developing human capabilities."
    }
    
    base_content = content_templates.get(domain, content_templates['Technology'])
    
    # Generate summary (first 5 sentences)
    sentences = base_content.split('. ')
    summary = '. '.join(sentences[:5]) + '.'
    
    return base_content, summary

def insert_full_dataset():
    """Insert complete dataset of 100 records"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔄 Inserting complete dataset of 100 publications...")
        
        # Clear existing data
        cursor.execute("DELETE FROM structured_content;")
        cursor.execute("DELETE FROM raw_html_store;")
        cursor.execute("DELETE FROM crawl_runs;")
        
        # Insert crawl run
        cursor.execute("""
            INSERT INTO crawl_runs (run_id, started_at, completed_at, status, total_urls, successful_extractions, failed_extractions)
            VALUES ('full_dataset_2025', NOW(), NOW(), 'completed', 100, 100, 0)
        """)
        
        # Insert raw HTML records and get their IDs
        raw_html_ids = []
        for i in range(1, 101):
            cursor.execute("""
                INSERT INTO raw_html_store (url, raw_html, headers, status_code, run_id)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (
                f'https://example.com/article-{i}',
                f'<html><body>Article {i} content</body></html>',
                json.dumps({"content-type": "text/html"}),
                200,
                'full_dataset_2025'
            ))
            raw_html_id = cursor.fetchone()[0]
            raw_html_ids.append(raw_html_id)
        
        # Insert structured content
        record_id = 1
        for author, primary_domain, article_count in AUTHORS:
            for i in range(article_count):
                # Select domain (mostly primary, sometimes others)
                if random.random() < 0.8:
                    domain = primary_domain
                else:
                    domain = random.choice(list(DOMAINS.keys()))
                
                # Select title template
                title_base = random.choice(TITLE_TEMPLATES.get(domain, TITLE_TEMPLATES['Technology']))
                title = f"{title_base} - Study {i+1}"
                
                # Generate content
                content, summary = generate_content(domain, title)
                
                # Select tags
                domain_tags = DOMAINS.get(domain, ['Technology'])
                selected_tags = random.sample(domain_tags, min(len(domain_tags), random.randint(1, 3)))
                
                # Generate publish date
                publish_date = date(2024, random.randint(1, 12), random.randint(1, 28))
                
                # Insert record using the corresponding raw_html_id
                cursor.execute("""
                    INSERT INTO structured_content 
                    (url, raw_html_id, domain, site_name, title, author, publish_date, content, summary, tags, run_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    f'https://example.com/article-{record_id}',
                    raw_html_ids[record_id - 1],  # Use the actual raw_html_id
                    domain,
                    f'{domain} Today',
                    title,
                    author,
                    publish_date,
                    content,
                    summary,
                    json.dumps(selected_tags),
                    'full_dataset_2025'
                ))
                
                record_id += 1
        
        conn.commit()
        
        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM structured_content")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT author, COUNT(*) FROM structured_content GROUP BY author ORDER BY author")
        author_counts = cursor.fetchall()
        
        print(f"✅ Successfully inserted {count} records")
        print("\n📊 Records per author:")
        for author, count in author_counts:
            print(f"  • {author}: {count} articles")
        
        # Show domain distribution
        cursor.execute("SELECT domain, COUNT(*) FROM structured_content GROUP BY domain ORDER BY domain")
        domain_counts = cursor.fetchall()
        
        print("\n🏷️ Records per domain:")
        for domain, count in domain_counts:
            print(f"  • {domain}: {count} articles")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error inserting data: {e}")
        return False

if __name__ == "__main__":
    success = insert_full_dataset()
    if success:
        print("\n🎉 Full dataset insertion completed successfully!")
        print("You can now proceed with the Neo4j migration.")
    else:
        print("\n💥 Dataset insertion failed. Check the error messages above.")