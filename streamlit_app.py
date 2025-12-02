#!/usr/bin/env python3

"""
RFP Studio - Streamlit RAG Frontend

Interactive web interface for document upload and Q&A processing.
Extracts questions from uploaded documents and generates answers using RAG.
"""

import streamlit as st
import asyncio
import tempfile
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# RFP Studio imports
from rfp_studio.config import get_settings
from rfp_studio.knowledge import load_knowledge_items, KnowledgeItem
from rfp_studio.vector import search_knowledge_base, embed_text
from rfp_studio.db import get_db

# Document processing
from document_processor import DocumentProcessor, QuestionExtractor, AnswerGenerator

# Configure Streamlit page
st.set_page_config(
    page_title="RFP Studio - Document Q&A",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processed_documents' not in st.session_state:
    st.session_state.processed_documents = []
if 'qa_results' not in st.session_state:
    st.session_state.qa_results = []
if 'knowledge_updated' not in st.session_state:
    st.session_state.knowledge_updated = False


class StreamlitRAGApp:
    """Main Streamlit RAG application for RFP Studio."""
    
    def __init__(self):
        self.doc_processor = DocumentProcessor()
        self.question_extractor = QuestionExtractor()
        self.answer_generator = AnswerGenerator()
        
    def render_header(self):
        """Render application header."""
        st.title("🚀 RFP Studio - Document Q&A")
        st.markdown("""
        **AI-powered document processing and question answering for RFP workflows**
        
        Upload RFP documents, extract questions automatically, and generate intelligent answers 
        using your organization's knowledge base.
        """)
        
    def render_sidebar(self):
        """Render sidebar with configuration and status."""
        st.sidebar.header("📋 Configuration")
        
        # Configuration status
        try:
            settings = get_settings()
            st.sidebar.success("✅ MongoDB Atlas connected")
            if settings.openai_api_key:
                st.sidebar.success("✅ OpenAI API configured")
            else:
                st.sidebar.warning("⚠️ OpenAI API key not set")
        except Exception as e:
            st.sidebar.error(f"❌ Configuration error: {str(e)}")
            
        # Processing options
        st.sidebar.header("🔧 Processing Options")
        
        auto_extract = st.sidebar.checkbox(
            "Auto-extract questions", 
            value=True, 
            help="Automatically detect and extract questions from uploaded documents"
        )
        
        auto_answer = st.sidebar.checkbox(
            "Auto-generate answers", 
            value=True, 
            help="Generate answers using RAG pipeline and knowledge base"
        )
        
        confidence_threshold = st.sidebar.slider(
            "Answer confidence threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Minimum confidence score for generated answers"
        )
        
        return {
            'auto_extract': auto_extract,
            'auto_answer': auto_answer,
            'confidence_threshold': confidence_threshold
        }
    
    def render_document_upload(self):
        """Render document upload section."""
        st.header("📄 Document Upload")
        
        uploaded_files = st.file_uploader(
            "Upload RFP documents (PDF, DOCX, TXT)",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Upload one or more RFP documents to process for questions and answers"
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in [doc['name'] for doc in st.session_state.processed_documents]:
                    # Process new document
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        doc_info = self._process_uploaded_file(uploaded_file)
                        if doc_info:
                            st.session_state.processed_documents.append(doc_info)
                            st.success(f"✅ Processed {uploaded_file.name}")
        
        # Display processed documents
        if st.session_state.processed_documents:
            st.subheader("📚 Processed Documents")
            for doc in st.session_state.processed_documents:
                with st.expander(f"📄 {doc['name']} ({doc['pages']} pages, {doc['questions']} questions)"):
                    st.write(f"**File size:** {doc['size']} bytes")
                    st.write(f"**Processing time:** {doc['processing_time']:.2f} seconds")
                    if doc['preview']:
                        st.write("**Content preview:**")
                        st.text(doc['preview'][:500] + "..." if len(doc['preview']) > 500 else doc['preview'])
                        
    def _process_uploaded_file(self, uploaded_file) -> Optional[Dict[str, Any]]:
        """Process an uploaded file and extract content."""
        try:
            import time
            start_time = time.time()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name
            
            try:
                # Extract text content
                text_content = self.doc_processor.extract_text(tmp_path)
                
                # Get document metadata
                pages = self.doc_processor.get_page_count(tmp_path)
                
                # Extract questions (if any)
                questions = self.question_extractor.extract_questions(text_content)
                
                processing_time = time.time() - start_time
                
                return {
                    'name': uploaded_file.name,
                    'size': uploaded_file.size,
                    'pages': pages,
                    'content': text_content,
                    'questions': len(questions),
                    'question_list': questions,
                    'processing_time': processing_time,
                    'preview': text_content[:1000]
                }
                
            finally:
                # Clean up temp file
                os.unlink(tmp_path)
                
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            return None
    
    def render_question_extraction(self, config):
        """Render question extraction and answering section."""
        if not st.session_state.processed_documents:
            st.info("📄 Upload documents above to begin question extraction and answering.")
            return
            
        st.header("❓ Question Extraction & Answering")
        
        # Select document to process
        doc_names = [doc['name'] for doc in st.session_state.processed_documents]
        selected_doc_name = st.selectbox("Select document to process:", doc_names)
        
        if selected_doc_name:
            selected_doc = next(doc for doc in st.session_state.processed_documents if doc['name'] == selected_doc_name)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if st.button("🔍 Extract Questions & Generate Answers", type="primary"):
                    self._process_questions_and_answers(selected_doc, config)
            
            with col2:
                if st.button("💾 Save to Knowledge Base"):
                    self._save_to_knowledge_base()
    
    def _process_questions_and_answers(self, doc: Dict[str, Any], config: Dict[str, Any]):
        """Process questions from document and generate answers."""
        try:
            questions = doc.get('question_list', [])
            
            if not questions:
                st.warning(f"No questions found in {doc['name']}")
                return
                
            st.subheader(f"📋 Processing {len(questions)} questions from {doc['name']}")
            
            qa_results = []
            progress_bar = st.progress(0)
            
            for i, question in enumerate(questions):
                with st.container():
                    st.write(f"**Question {i+1}:** {question}")
                    
                    if config['auto_answer']:
                        with st.spinner("Generating answer..."):
                            # Generate answer using RAG
                            answer_result = self.answer_generator.generate_answer(
                                question, 
                                confidence_threshold=config['confidence_threshold']
                            )
                            
                            if answer_result['success']:
                                st.success(f"**Answer:** {answer_result['answer']}")
                                st.caption(f"Confidence: {answer_result['confidence']:.2f}")
                                
                                qa_results.append({
                                    'question': question,
                                    'answer': answer_result['answer'],
                                    'confidence': answer_result['confidence'],
                                    'sources': answer_result.get('sources', [])
                                })
                            else:
                                st.error(f"Failed to generate answer: {answer_result.get('error', 'Unknown error')}")
                    else:
                        # Manual answer input
                        manual_answer = st.text_area(f"Enter answer for Question {i+1}:", key=f"answer_{i}")
                        if manual_answer:
                            qa_results.append({
                                'question': question,
                                'answer': manual_answer,
                                'confidence': 1.0,
                                'sources': ['Manual input']
                            })
                
                progress_bar.progress((i + 1) / len(questions))
            
            # Store results in session state
            st.session_state.qa_results = qa_results
            
            if qa_results:
                st.success(f"✅ Successfully processed {len(qa_results)} Q&A pairs!")
                
        except Exception as e:
            st.error(f"Error processing questions: {str(e)}")
    
    def _save_to_knowledge_base(self):
        """Save Q&A results to the knowledge base."""
        if not st.session_state.qa_results:
            st.warning("No Q&A results to save. Process questions first.")
            return
            
        try:
            with st.spinner("Saving to knowledge base..."):
                knowledge_items = []
                
                for qa in st.session_state.qa_results:
                    # Create knowledge item
                    knowledge_item = KnowledgeItem(
                        text=f"Q: {qa['question']} A: {qa['answer']}",
                        team_key="sme_team_rfp_processed",
                        topic="RFP Document Processing",
                        tags=["rfp", "document_processing", "rag"],
                        extra={
                            'question': qa['question'],
                            'answer': qa['answer'],
                            'confidence': qa['confidence'],
                            'sources': qa['sources'],
                            'processing_method': 'streamlit_rag'
                        }
                    )
                    knowledge_items.append(knowledge_item)
                
                # Load into knowledge base
                inserted_ids = load_knowledge_items(knowledge_items)
                
                st.success(f"✅ Saved {len(inserted_ids)} Q&A pairs to knowledge base!")
                st.session_state.knowledge_updated = True
                
                # Show inserted IDs
                with st.expander("📝 Saved Knowledge Items"):
                    for i, item_id in enumerate(inserted_ids):
                        qa = st.session_state.qa_results[i]
                        st.write(f"**ID:** {item_id}")
                        st.write(f"**Q:** {qa['question'][:100]}...")
                        st.write(f"**A:** {qa['answer'][:100]}...")
                        st.write("---")
                        
        except Exception as e:
            st.error(f"Error saving to knowledge base: {str(e)}")
    
    def render_knowledge_base_status(self):
        """Render knowledge base status and search."""
        st.header("🧠 Knowledge Base")
        
        if st.session_state.knowledge_updated:
            st.success("✅ Knowledge base updated with new Q&A pairs!")
        
        # Knowledge base search
        search_query = st.text_input("🔍 Search knowledge base:", placeholder="Enter search query...")
        
        if search_query and st.button("Search"):
            try:
                with st.spinner("Searching knowledge base..."):
                    # Embed the search query
                    query_embedding = embed_text(search_query)
                    
                    # Search knowledge base
                    results = search_knowledge_base(query_embedding, limit=5)
                    
                    if results:
                        st.subheader(f"📋 Search Results ({len(results)} found)")
                        
                        for i, result in enumerate(results):
                            with st.expander(f"Result {i+1} (Score: {result.get('score', 0):.3f})"):
                                st.write(f"**Team:** {result.get('team_key', 'Unknown')}")
                                st.write(f"**Topic:** {result.get('topic', 'Unknown')}")
                                st.write(f"**Content:** {result.get('text', 'No content')[:300]}...")
                                if result.get('tags'):
                                    st.write(f"**Tags:** {', '.join(result['tags'])}")
                    else:
                        st.info("No results found. Try a different search term.")
                        
            except Exception as e:
                st.error(f"Search error: {str(e)}")
    
    def run(self):
        """Run the Streamlit application."""
        self.render_header()
        config = self.render_sidebar()
        
        # Main tabs
        tab1, tab2, tab3 = st.tabs(["📄 Upload & Process", "❓ Q&A Results", "🧠 Knowledge Base"])
        
        with tab1:
            self.render_document_upload()
            self.render_question_extraction(config)
        
        with tab2:
            if st.session_state.qa_results:
                st.header("📋 Q&A Results")
                
                for i, qa in enumerate(st.session_state.qa_results):
                    with st.expander(f"Q&A Pair {i+1} (Confidence: {qa['confidence']:.2f})"):
                        st.write(f"**Question:** {qa['question']}")
                        st.write(f"**Answer:** {qa['answer']}")
                        if qa.get('sources'):
                            st.write(f"**Sources:** {', '.join(qa['sources'])}")
            else:
                st.info("No Q&A results yet. Process documents in the Upload & Process tab.")
        
        with tab3:
            self.render_knowledge_base_status()


def main():
    """Main entry point for Streamlit app."""
    try:
        app = StreamlitRAGApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    main()