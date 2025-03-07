import typer
from typing_extensions import Annotated
from pathlib import Path
from . import __version__
from . import db
from .core import download_transcript, chunk_transcript
from .llm import summarize_transcript, YTSummarize
from .embeddings import generate_embeddings, get_query_embedding

app = typer.Typer(help="Build knowledge base from YouTube video transcripts")

def version_callback(value: bool):
    if value:
        typer.echo(f"ytq version: {__version__}")
        raise typer.Exit()

@app.callback()
def callback(
    version: Annotated[
        bool, typer.Option("--version", callback=version_callback, is_eager=True)
    ] = False,
):
    """
    ytq: Build knowledge base from YouTube video transcripts
    """

@app.command()
def add(
    url: Annotated[str, typer.Argument(help="YouTube video URL to process")],
    chunk_size: Annotated[int, typer.Option(help="Max size of each chunk in charactes")] = 1000,
    chunk_overlap: Annotated[int, typer.Option(help="Overlap between chunks, in characters")] = 100,
    provider: Annotated[str, typer.Option(help="LLM summarization provider to use")] = "openai",
    model: Annotated[str, typer.Option(help="LLM summarization model to use")] = "gpt-4o-mini",
):
    """
    Add a YouTube video to the knowledge base
    """
    from rich.progress import Progress
    typer.echo(f"Processing video: {url}")
    with Progress() as progress:
        task = progress.add_task("[cyan]Starting processing...", total=5)

        # Database initialization step
        db_path = Path("ytq.db")
        if not db_path.exists():
            progress.update(task, description="[yellow]Initializing database for the first time...")
            db.init_db()
        progress.advance(task)

        # Download transcript
        progress.update(task, description="[cyan]Downloading transcript...")
        vid_transcript = download_transcript(url)
        progress.advance(task)

        # Chunk transcript
        progress.update(task, description="[cyan]Chunking transcript...")
        vid_chunks = chunk_transcript(vid_transcript)
        progress.advance(task)

        # LLM summarization
        progress.update(task, description="[cyan]Generating summary with LLM...")
        vid_summary = summarize_transcript(vid_chunks, vid_transcript['metadata'], YTSummarize, provider=provider, model=model)
        progress.advance(task)

        # Embedding generation
        progress.update(task, description="[cyan]Generating embeddings...")
        vid_embeddings = generate_embeddings(vid_chunks)
        progress.advance(task)

        db.store_video(vid_transcript, vid_summary, vid_embeddings)

    typer.echo("Video processed successfully!")

@app.command()
def query(
    search_term: Annotated[str, typer.Argument(help="Search term to query the knowledge base")],
    chunks: Annotated[bool, typer.Option(help="Enable chunk-level search")] = False,
    semantic: Annotated[bool, typer.Option(help="Enable semantic search (when chunk search enabled only)")] = False,
    limit: Annotated[int, typer.Option(help="Maximum number of results")] = 3
):
    """
    Search the knowledge base
    """
    from rich.console import Console
    from rich.table import Table
    from rich.markdown import Markdown
    
    console = Console()
    
    typer.echo(f"Searching for: {search_term}")
    
    # Initialize DB if it doesn't exist
    db_path = Path("~/.ytq/ytq.db").expanduser()
    if not db_path.exists():
        console.print("[yellow]Initializing database for the first time...[/]")
        db.init_db()
    
    if chunks:
        # Chunk-level search
        console.print(f"[cyan]Performing {'semantic' if semantic else 'keyword'} chunk search...[/]")
        
        if semantic:
            # Generate embedding for the search query
            embedding = get_query_embedding(search_term)
            
            # Hybrid search using both keywords and embeddings
            results = db.hybrid_search_chunks(search_term, embedding, limit=limit)
            
            if not results:
                console.print("[yellow]No results found.[/]")
                return
            
            # Display results
            table = Table(title=f"Semantic Search Results for '{search_term}'")
            table.add_column("Video ID", style="cyan")
            table.add_column("Video", style="cyan")
            table.add_column("Chunk", style="green")
            table.add_column("Score", justify="right", style="magenta")
            table.add_column("Time", style="blue")
            
            for result in results:
                timestamp = result["timestamp"]
                time_str = f"{int(timestamp // 60)}:{int(timestamp % 60):02d}"
                video_url = f"{result['url']}&t={int(timestamp)}"
                table.add_row(
                    result['video_id'],
                    f"[link={video_url}]{result['title']}[/link]", 
                    result["chunk_text"][:80] + "..." if len(result["chunk_text"]) > 80 else result["chunk_text"],
                    f"{result['rrf_score']:.4f}",
                    time_str
                )
                
            console.print(table)
            
        else:
            # Regular keyword search for chunks
            results = db.search_chunks(search_term, limit=limit)
            
            if not results:
                console.print("[yellow]No results found.[/]")
                return
            
            # Display results
            table = Table(title=f"Search Results for '{search_term}'")
            table.add_column("Video ID", style="cyan")
            table.add_column("Video", style="cyan")
            table.add_column("Chunk", style="green")
            table.add_column("Time", style="blue")
            
            for result in results:
                timestamp = result["timestamp"]
                time_str = f"{int(timestamp // 60)}:{int(timestamp % 60):02d}"
                video_url = f"{result['url']}&t={int(timestamp)}"
                table.add_row(
                    result['video_id'],
                    f"[link={video_url}]{result['title']}[/link]", 
                    result["chunk_text"][:80] + "..." if len(result["chunk_text"]) > 80 else result["chunk_text"],
                    time_str
                )
                
            console.print(table)
    else:
        # Video-level search
        console.print(f"[cyan]Performing video search...[/]")
        results = db.search_videos(search_term, limit=limit)
        
        if not results:
            console.print("[yellow]No results found.[/]")
            return
            
        # Display results
        for i, video in enumerate(results):
            console.print(f"\n[bold cyan]{i+1}. {video['title']}[/bold cyan] by {video['author']}")
            console.print(f"[blue link={video['url']}]{video['url']}[/blue link]")
            
            if video.get('tldr'):
                console.print(f"[bold]TL;DR:[/bold] {video['tldr']}")
                
            if video.get('tags') and len(video['tags']) > 0:
                tags = " ".join([f"[blue]#{tag}[/blue]" for tag in video['tags']])
                console.print(f"\n{tags}")
                
            if i < len(results) - 1:
                console.print("\n" + "-" * 50)


@app.command(context_settings={"ignore_unknown_options": True})
def summary(
    video_id: Annotated[str, typer.Argument(help="Video ID to display summary for")]
):
    """
    Display summary for a video
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    
    console = Console()
    
    # Initialize DB if it doesn't exist
    db_path = Path("~/.ytq/ytq.db").expanduser()
    if not db_path.exists():
        console.print("[yellow]Initializing database for the first time...[/]")
        db.init_db()
    
    # Retrieve video data from database
    video = db.get_video(video_id)
    
    if not video:
        console.print(f"[red]Video with ID '{video_id}' not found in the database.[/]")
        raise typer.Exit(code=1)
    
    # Display video information
    console.print(f"\n[bold cyan]{video['title']}[/bold cyan] by {video['author']}")
    
    # Format video URL and display as clickable link
    video_url = video.get('url', f"https://youtube.com/watch?v={video_id}")
    console.print(f"[blue link={video_url}]{video_url}[/blue link]")
    
    # Display TLDR if available
    if video.get('tldr'):
        console.print(f"\n[bold]TL;DR:[/bold] {video['tldr']}")
    
    # Display video description if available
    if video.get('video_description'):
        console.print(f"\n[bold]Description:[/bold]")
        console.print(video['video_description'])

    # Display full summary in a panel
    if video.get('summary'):
        console.print("\n[bold]Summary:[/bold]")
        console.print(Panel(video['summary'], expand=False))
    
    # Display tags if available
    if video.get('tags') and len(video['tags']) > 0:
        tags = " ".join([f"[blue]#{tag}[/blue]" for tag in video['tags']])
        console.print(f"\n{tags}")
    
    # Display additional metadata
    upload_date = video.get('upload_date', '')
    if upload_date and len(upload_date) == 8:  # Format YYYYMMDD
        formatted_date = f"{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
        console.print(f"\n[dim]Uploaded on: {formatted_date}[/dim]")
    
    duration_min = video.get('duration', 0) // 60
    duration_sec = video.get('duration', 0) % 60
    console.print(f"[dim]Duration: {duration_min}:{duration_sec:02d}[/dim]")
    
    if video.get('view_count'):
        console.print(f"[dim]Views: {video.get('view_count', 0):,}[/dim]")
    
    console.print(f"[dim]Processed at: {video.get('processed_at', '')}[/dim]")


@app.command(context_settings={"ignore_unknown_options": True})
def delete(
    video_id: Annotated[str, typer.Argument(help="Video ID to display summary for")]
):
    """
    Delete a video from the database
    """
    db.delete_video(video_id)
    typer.echo(f"Video with ID '{video_id}' deleted from the database.")

if __name__ == "__main__":
    app()
