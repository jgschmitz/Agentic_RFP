#!/usr/bin/env python3

"""
RFP Studio CLI - Simple command-line interface for RFP automation.

This provides basic CLI commands to demonstrate the RFP Studio functionality.
"""

import asyncio
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from rfp_studio import run_flow, run_sales_only, run_bdm_only, run_sme_router_only
from rfp_studio.knowledge import load_sample_knowledge, clear_knowledge_base
from rfp_studio.config import get_settings

app = typer.Typer(name="rfp-studio", help="RFP Studio CLI - AI-orchestrated RFP automation")
console = Console()


@app.command()
def create_rfp(
    title: str = typer.Option(..., "--title", "-t", help="RFP title"),
    client_name: str = typer.Option(..., "--client", "-c", help="Client name"),
    client_contact: Optional[str] = typer.Option(None, "--contact", help="Client contact email"),
    industry: Optional[str] = typer.Option(None, "--industry", help="Client industry"),
    size: Optional[str] = typer.Option("Medium", "--size", help="RFP size (Small/Medium/Large)"),
):
    """Create a new RFP and run the basic workflow."""
    
    payload = {
        "title": title,
        "client_name": client_name,
        "client_contact": client_contact,
        "industry": industry,
        "rfp_size": size,
    }
    
    console.print(f"🚀 Creating RFP: '{title}' for {client_name}")
    
    try:
        result = asyncio.run(run_flow(payload=payload))
        
        # Extract RFP ID from result
        rfp_id = None
        changes = result.get("agent_changes", [])
        if changes and changes[0].get("rfp", {}).get("id"):
            rfp_id = changes[0]["rfp"]["id"]
        
        console.print("✅ RFP workflow completed successfully!")
        if rfp_id:
            console.print(f"📄 RFP ID: {rfp_id}")
            
        # Show summary table
        table = Table(title="Workflow Results")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Message", style="yellow")
        
        events = result.get("agent_events", [])
        for i, event_dict in enumerate(events):
            agent_name = f"Agent {i+1}"
            status = "Completed"
            message = str(event_dict)[:50] + "..." if len(str(event_dict)) > 50 else str(event_dict)
            table.add_row(agent_name, status, message)
            
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error creating RFP: {str(e)}")
        sys.exit(1)


@app.command()
def setup_knowledge():
    """Load sample knowledge base for SME routing."""
    
    console.print("📚 Loading sample knowledge base...")
    
    try:
        # Clear existing knowledge
        cleared = clear_knowledge_base()
        console.print(f"🗑️ Cleared {cleared} existing knowledge items")
        
        # Load sample knowledge
        inserted_ids = load_sample_knowledge()
        console.print(f"✅ Loaded {len(inserted_ids)} knowledge items")
        
        # Show knowledge items in a table
        table = Table(title="Knowledge Base Items")
        table.add_column("Item", style="cyan")
        table.add_column("Team", style="green")
        table.add_column("Topic", style="yellow")
        
        knowledge_items = [
            ("Security & Compliance", "sme_team_security", "SOC2, HIPAA, PCI compliance"),
            ("Support & SLA", "sme_team_support", "24/7 support, response times"),
            ("Pricing & Licensing", "sme_team_sales", "Subscription tiers, discounts"),
            ("Technical Implementation", "sme_team_technical", "API integration, migration"),
            ("Legal & Contracts", "sme_team_legal", "Contract negotiations, data protection"),
        ]
        
        for item, team, topic in knowledge_items:
            table.add_row(item, team, topic)
            
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error setting up knowledge base: {str(e)}")
        sys.exit(1)


@app.command()
def run_agent(
    agent: str = typer.Argument(..., help="Agent to run: sales, bdm, sme_router"),
    rfp_id: Optional[str] = typer.Option(None, "--rfp-id", help="RFP ID (required for bdm)"),
):
    """Run a specific agent individually."""
    
    console.print(f"🤖 Running {agent} agent...")
    
    try:
        if agent == "sales":
            # Example sales payload
            payload = {
                "title": "Test RFP",
                "client_name": "Example Corp",
                "client_contact": "test@example.com",
            }
            result = asyncio.run(run_sales_only(payload=payload))
            
        elif agent == "bdm":
            if not rfp_id:
                console.print("❌ BDM agent requires --rfp-id parameter")
                sys.exit(1)
                
            # Example BDM payload
            payload = {
                "sections": [
                    {
                        "title": "Executive Summary",
                        "description": "High-level overview of our capabilities",
                        "suggested_team": "sme_team_sales",
                        "task_type": "CONTENT_DRAFT"
                    },
                    {
                        "title": "Security Questions",
                        "description": "SOC2 and compliance requirements",
                        "suggested_team": "sme_team_security", 
                        "task_type": "SME_QA"
                    }
                ]
            }
            result = asyncio.run(run_bdm_only(rfp_id=rfp_id, payload=payload))
            
        elif agent == "sme_router":
            # Example SME routing payload
            payload = {
                "questions": [
                    {
                        "task_id": "example_task_id",
                        "text": "What are your security compliance certifications?"
                    }
                ]
            }
            result = asyncio.run(run_sme_router_only(payload=payload, rfp_id=rfp_id))
            
        else:
            console.print(f"❌ Unknown agent: {agent}")
            console.print("Available agents: sales, bdm, sme_router")
            sys.exit(1)
            
        console.print(f"✅ {agent} agent completed!")
        console.print(f"📊 Result: {result.message}")
        
    except Exception as e:
        console.print(f"❌ Error running {agent} agent: {str(e)}")
        sys.exit(1)


@app.command()
def config():
    """Show current configuration."""
    
    try:
        settings = get_settings()
        
        table = Table(title="RFP Studio Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("MongoDB URI", settings.mongodb_uri[:50] + "..." if len(settings.mongodb_uri) > 50 else settings.mongodb_uri)
        table.add_row("Database Name", settings.mongodb_db_name)
        table.add_row("OpenAI API Key", "✅ Set" if settings.openai_api_key else "❌ Not set")
        table.add_row("RFP Vector Index", settings.atlas_vector_index_rfps)
        table.add_row("KB Vector Index", settings.atlas_vector_index_kb)
        table.add_row("Environment", settings.env)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error reading configuration: {str(e)}")
        sys.exit(1)


@app.command()
def example():
    """Run a complete example workflow."""
    
    console.print("🎯 Running complete RFP Studio example...")
    console.print("This will:")
    console.print("1. Setup knowledge base")
    console.print("2. Create a sample RFP")
    console.print("3. Run the full workflow")
    
    try:
        # Step 1: Setup knowledge base
        console.print("\n📚 Step 1: Setting up knowledge base...")
        clear_knowledge_base()
        inserted_ids = load_sample_knowledge()
        console.print(f"✅ Loaded {len(inserted_ids)} knowledge items")
        
        # Step 2: Create RFP
        console.print("\n🚀 Step 2: Creating sample RFP...")
        payload = {
            "title": "Enterprise Cloud Platform RFP",
            "client_name": "Global Tech Solutions",
            "client_contact": "procurement@globaltech.com",
            "industry": "Technology",
            "rfp_size": "Large",
        }
        
        result = asyncio.run(run_flow(payload=payload))
        
        console.print("✅ Complete workflow finished!")
        console.print(f"🎉 This demonstrates the full RFP Studio capabilities!")
        
        # Show final summary
        rprint("\n[bold green]🎊 Example completed successfully![/bold green]")
        rprint("Your RFP Studio skeletal implementation is ready for customer demo!")
        
    except Exception as e:
        console.print(f"❌ Error running example: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    app()