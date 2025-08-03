#!/usr/bin/env python3
"""
Trending Content Analyzer using LangGraph
Analyzes article titles and snippets to identify topics, tags, and community classification
"""

import pandas as pd
import yaml
import os
import time
import tiktoken
from typing import Dict, List, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage
import json

class AnalysisState(TypedDict):
    """State for the analysis workflow"""
    article_title: str
    article_snippet: str
    topic: str
    tags: List[str]
    community: str
    thought_process_determining_topic: str
    classification_reason: str
    topic_llm_time: float
    topic_input_tokens: int
    topic_output_tokens: int
    classification_llm_time: float
    classification_input_tokens: int
    classification_output_tokens: int
    analysis_complete: bool

class TrendingAnalyzer:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the analyzer with configuration"""
        self.config = self.load_config(config_path)
        self.llm = self.setup_llm()
        self.workflow = self.create_workflow()
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def setup_llm(self):
        """Setup the language model based on configuration"""
        model_config = self.config['model']
        
        if model_config['provider'] == 'openai':
            self.tokenizer = tiktoken.encoding_for_model(model_config['name'])
            return ChatOpenAI(
                model=model_config['name'],
                api_key=model_config['api_key'],
                temperature=model_config['temperature'],
                max_tokens=model_config['max_tokens']
            )
        elif model_config['provider'] == 'anthropic':
            # For Anthropic, we'll use a rough estimation
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            return ChatAnthropic(
                model=model_config['name'],
                api_key=model_config['api_key'],
                temperature=model_config['temperature'],
                max_tokens=model_config['max_tokens']
            )
        else:
            raise ValueError(f"Unsupported provider: {model_config['provider']}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.tokenizer.encode(text))
        except:
            # Fallback: rough estimation (4 chars per token)
            return len(text) // 4
    
    def identify_topic_and_tags(self, state: AnalysisState) -> AnalysisState:
        """Node to identify topic and generate tags"""
        system_prompt = """You are an expert content analyst. Analyze the given article title and snippet to:
        1. Identify the main topic/theme
        2. Generate relevant tags (3-5 tags)
        3. Provide your thought process for determining the topic (ONE SENTENCE ONLY)
        
        Return your response in JSON format:
        {
            "topic": "main topic identified",
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
            "thought_process_determining_topic": "One sentence explaining your reasoning for this topic and tags"
        }
        
       """
        
        user_prompt = f"""
        Article Title: {state['article_title']}
        Article Snippet: {state['article_snippet']}
        
        Please analyze and provide the topic, tags, and your thought process in JSON format.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Calculate input tokens
        input_text = f"{system_prompt}\n{user_prompt}"
        input_tokens = self.count_tokens(input_text)
        
        # Retry logic - attempt twice before failing
        for attempt in range(2):
            try:
                start_time = time.time()
                response = self.llm.invoke(messages)
                end_time = time.time()
                
                # Calculate metrics
                llm_time = end_time - start_time
                output_tokens = self.count_tokens(response.content)
                
                # Clean the response content to extract JSON
                content = response.content.strip()
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()
                
                result = json.loads(content)
                
                # Validate required fields
                if 'topic' not in result or 'tags' not in result:
                    raise ValueError("Missing required fields in response")
                
                state['topic'] = result['topic']
                state['tags'] = result['tags']
                state['thought_process_determining_topic'] = result.get('thought_process_determining_topic', 'No reasoning provided')
                state['topic_llm_time'] = llm_time
                state['topic_input_tokens'] = input_tokens
                state['topic_output_tokens'] = output_tokens
                
                print(f"Topic LLM call: {llm_time:.2f}s, Input: {input_tokens} tokens, Output: {output_tokens} tokens")
                return state
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Attempt {attempt + 1} failed for topic identification: {e}")
                if 'response' in locals():
                    print(f"Response content: {response.content[:200]}...")
                
                if attempt == 1:  # Second attempt failed
                    print(f"TERMINATING: Failed to get valid response for article: {state['article_title'][:50]}...")
                    raise Exception(f"LLM failed to provide valid topic analysis after 2 attempts: {str(e)}")
        
        return state
    
    def classify_community(self, state: AnalysisState) -> AnalysisState:
        """Node to classify content for B2B, B2C, or Hybrid communities"""
        system_prompt = """You are a business analyst specializing in audience segmentation. 
        Based on the article topic, title, and snippet, classify the content for the most appropriate community:
        
        - B2B: Content primarily useful for businesses, professionals, service providers, financial advisors, etc.
        - B2C: Content primarily useful for individual consumers, retirees, personal finance, lifestyle
        - Hybrid: Content useful for both businesses and consumers
        
        Consider:
        - Who would find this content most valuable?
        - Is it about personal decisions or business strategies?
        - Does it serve both audiences equally?
        
        Return your response in JSON format:
        {
            "community": "B2B, B2C, or Hybrid",
            "classification_reason": "One sentence explaining your reasoning for this classification"
        }"""
        
        user_prompt = f"""
        Topic: {state['topic']}
        Article Title: {state['article_title']}
        Article Snippet: {state['article_snippet']}
        Tags: {', '.join(state['tags'])}
        
        Classify this content and provide your reasoning in JSON format.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Calculate input tokens
        input_text = f"{system_prompt}\n{user_prompt}"
        input_tokens = self.count_tokens(input_text)
        
        # Retry logic - attempt twice before failing
        for attempt in range(2):
            try:
                start_time = time.time()
                response = self.llm.invoke(messages)
                end_time = time.time()
                
                # Calculate metrics
                llm_time = end_time - start_time
                output_tokens = self.count_tokens(response.content)
                
                # Clean the response content to extract JSON
                content = response.content.strip()
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()
                
                result = json.loads(content)
                
                # Validate required fields and community value
                if 'community' not in result:
                    raise ValueError("Missing community field in response")
                
                community = result['community'].strip().upper()
                if community not in ['B2B', 'B2C', 'HYBRID']:
                    raise ValueError(f"Invalid community value: {community}")
                
                state['community'] = community
                state['classification_reason'] = result.get('classification_reason', 'No reasoning provided')
                state['classification_llm_time'] = llm_time
                state['classification_input_tokens'] = input_tokens
                state['classification_output_tokens'] = output_tokens
                state['analysis_complete'] = True
                
                print(f"Classification LLM call: {llm_time:.2f}s, Input: {input_tokens} tokens, Output: {output_tokens} tokens")
                return state
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Attempt {attempt + 1} failed for community classification: {e}")
                if 'response' in locals():
                    print(f"Response content: {response.content[:200]}...")
                
                if attempt == 1:  # Second attempt failed
                    print(f"TERMINATING: Failed to get valid classification for article: {state['article_title'][:50]}...")
                    raise Exception(f"LLM failed to provide valid community classification after 2 attempts: {str(e)}")
        
        return state
    
    def create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(AnalysisState)
        
        # Add nodes
        workflow.add_node("identify_topic_tags", self.identify_topic_and_tags)
        workflow.add_node("classify_community", self.classify_community)
        
        # Add edges
        workflow.add_edge("identify_topic_tags", "classify_community")
        workflow.add_edge("classify_community", END)
        
        # Set entry point
        workflow.set_entry_point("identify_topic_tags")
        
        return workflow.compile()
    
    def analyze_article(self, title: str, snippet: str) -> Dict:
        """Analyze a single article"""
        initial_state = AnalysisState(
            article_title=title,
            article_snippet=snippet,
            topic="",
            tags=[],
            community="",
            thought_process_determining_topic="",
            classification_reason="",
            topic_llm_time=0.0,
            topic_input_tokens=0,
            topic_output_tokens=0,
            classification_llm_time=0.0,
            classification_input_tokens=0,
            classification_output_tokens=0,
            analysis_complete=False
        )
        
        result = self.workflow.invoke(initial_state)
        
        return {
            'topic': result['topic'],
            'tags': result['tags'],
            'community': result['community'],
            'thought_process_determining_topic': result['thought_process_determining_topic'],
            'classification_reason': result['classification_reason'],
            'topic_llm_time': result['topic_llm_time'],
            'topic_input_tokens': result['topic_input_tokens'],
            'topic_output_tokens': result['topic_output_tokens'],
            'classification_llm_time': result['classification_llm_time'],
            'classification_input_tokens': result['classification_input_tokens'],
            'classification_output_tokens': result['classification_output_tokens']
        }
    
    def process_csv(self, input_file: str = "trending.csv", output_file: str = "trending.csv"):
        """Process the entire CSV file"""
        print(f"Loading data from {input_file}...")
        df = pd.read_csv(input_file)
        
        print(f"Processing {len(df)} articles...")
        
        # Initialize new columns
        df['community'] = ''
        df['tags'] = ''
        df['thought_process_determining_topic'] = ''
        df['classification_reason'] = ''
        df['topic_llm_time'] = 0.0
        df['topic_input_tokens'] = 0
        df['topic_output_tokens'] = 0
        df['classification_llm_time'] = 0.0
        df['classification_input_tokens'] = 0
        df['classification_output_tokens'] = 0
        
        # Process each row
        for index, row in df.iterrows():
            print(f"Processing article {index + 1}/{len(df)}: {row['article_title'][:50]}...")
            
            try:
                result = self.analyze_article(
                    title=row['article_title'],
                    snippet=row['article_snippet']
                )
                
                df.at[index, 'community'] = result['community']
                df.at[index, 'tags'] = ', '.join(result['tags'])
                df.at[index, 'thought_process_determining_topic'] = result['thought_process_determining_topic']
                df.at[index, 'classification_reason'] = result['classification_reason']
                df.at[index, 'topic_llm_time'] = result['topic_llm_time']
                df.at[index, 'topic_input_tokens'] = result['topic_input_tokens']
                df.at[index, 'topic_output_tokens'] = result['topic_output_tokens']
                df.at[index, 'classification_llm_time'] = result['classification_llm_time']
                df.at[index, 'classification_input_tokens'] = result['classification_input_tokens']
                df.at[index, 'classification_output_tokens'] = result['classification_output_tokens']
                
            except Exception as e:
                print(f"CRITICAL ERROR processing article {index + 1}: {e}")
                print(f"Article title: {row['article_title']}")
                print("TERMINATING PROCESS - LLM failed to provide valid response after retries")
                
                # Save partial results before terminating
                if index > 0:
                    partial_output = output_file.replace('.csv', f'_partial_{index}_articles.csv')
                    df.iloc[:index].to_csv(partial_output, index=False)
                    print(f"Partial results saved to: {partial_output}")
                
                raise e
        
        # Save the updated CSV
        print(f"Saving results to {output_file}...")
        df.to_csv(output_file, index=False)
        print("Analysis complete!")
        
        # Print summary
        community_counts = df['community'].value_counts()
        print("\nCommunity Distribution:")
        for community, count in community_counts.items():
            print(f"  {community}: {count} articles")

def main():
    """Main execution function"""
    try:
        analyzer = TrendingAnalyzer()
        analyzer.process_csv()
    except Exception as e:
        print(f"Error: {e}")
        print("Please ensure config.yaml is properly configured with your API key.")

if __name__ == "__main__":
    main()