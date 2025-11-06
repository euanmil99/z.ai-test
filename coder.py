from typing import List, Dict, Any
from ..core import BaseAgent, Task
from loguru import logger
import asyncio
import subprocess
import tempfile
import os
import sys
from pathlib import Path

class CodeExecutorAgent(BaseAgent):
    def __init__(self, agent_id: str = None, name: str = None):
        super().__init__(agent_id, name or "CodeExecutorAgent")
        self.temp_dir = None
        self.allowed_languages = ["python", "javascript", "bash", "html", "css", "powershell", "php", "ruby"]
    
    def get_capabilities(self) -> List[str]:
        return ["code_execution", "script_running", "code_generation", "file_operations"]
    
    def _initialize_tools(self):
        """Initialize code execution tools"""
        self.tools = {
            "execute_python": self.execute_python_code,
            "execute_javascript": self.execute_javascript_code,
            "execute_bash": self.execute_bash_command,
            "generate_code": self.generate_code_with_zai
        }
    
    async def process_task(self, task: Task) -> Any:
        """Optimized code execution task processing"""
        try:
            parameters = task.parameters
            code = parameters.get("code", "")
            language = parameters.get("language", "python").lower()
            files = parameters.get("files", {})
            input_data = parameters.get("input", "")
            timeout = parameters.get("timeout", 60)  # Increased for autonomy
            auto_generate = parameters.get("auto_generate", False)
            
            # Auto-generate code if not provided
            if not code and auto_generate:
                code = await self.generate_code_with_zai(task.description, language)
                if not code:
                    raise ValueError("Failed to generate code")
            
            # Validate language (relaxed - allow more languages)
            if language not in self.allowed_languages:
                logger.warning(f"Language '{language}' not in standard list, attempting execution anyway")
            
            # Create temporary workspace
            await self._setup_workspace()
            
            # Create files if provided
            if files:
                for filename, content in files.items():
                    await self.create_file(filename, content)
            
            # Execute code with enhanced capabilities
            if language == "python":
                result = await self.execute_python_code(code, input_data, timeout)
            elif language == "javascript":
                result = await self.execute_javascript_code(code, input_data, timeout)
            elif language == "bash":
                result = await self.execute_bash_command(code, timeout)
            elif language in ["html", "css"]:
                result = await self.handle_web_code(code, language)
            else:
                result = await self.execute_generic_code(code, language, timeout)
            
            # Use ZAI to analyze results
            if result.get("success") and self.zai_client:
                result["zai_analysis"] = await self._analyze_execution_result(code, result)
            
            return {
                "language": language,
                "execution_result": result,
                "files_created": list(files.keys()) if files else [],
                "temp_directory": self.temp_dir,
                "auto_generated": auto_generate and not parameters.get("code", "")
            }
            
        except Exception as e:
            logger.error(f"Code execution failed: {str(e)}")
            raise e
        finally:
            await self._cleanup_workspace()
    
    async def _setup_workspace(self):
        """Setup enhanced temporary workspace"""
        self.temp_dir = tempfile.mkdtemp(prefix="swarmforge_code_")
        # Create additional directories for enhanced functionality
        os.makedirs(os.path.join(self.temp_dir, "output"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "temp"), exist_ok=True)
    
    async def _cleanup_workspace(self):
        """Cleanup workspace"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup workspace: {str(e)}")
    
    async def generate_code_with_zai(self, requirement: str, language: str = "python") -> str:
        """Generate code using ZAI"""
        if not self.zai_client:
            return f"# Code generation unavailable\n# Requirement: {requirement}"
        
        try:
            prompt = f"""Generate {language} code for: {requirement}
Provide only executable code, no explanations."""
            
            code = await self.zai_client.generate_code(requirement, language)
            return code or f"# Failed to generate code for: {requirement}"
        except Exception as e:
            logger.warning(f"Code generation failed: {str(e)}")
            return f"# Code generation failed: {str(e)}\n# Requirement: {requirement}"
    
    async def execute_python_code(self, code: str, input_data: str = "", timeout: int = 60) -> Dict[str, Any]:
        """Enhanced Python code execution"""
        try:
            py_file = os.path.join(self.temp_dir, "script.py")
            with open(py_file, 'w') as f:
                f.write(code)
            
            # Enhanced execution with more privileges
            process = await asyncio.create_subprocess_exec(
                sys.executable, py_file,
                cwd=self.temp_dir,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # Allow network access and other capabilities
                env={**os.environ, "PYTHONPATH": self.temp_dir}
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data.encode()),
                timeout=timeout
            )
            
            return {
                "return_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "success": process.returncode == 0
            }
            
        except asyncio.TimeoutError:
            return {
                "error": "Execution timed out",
                "timeout": timeout,
                "success": False
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    async def execute_javascript_code(self, code: str, input_data: str = "", timeout: int = 60) -> Dict[str, Any]:
        """Enhanced JavaScript execution"""
        try:
            js_file = os.path.join(self.temp_dir, "script.js")
            with open(js_file, 'w') as f:
                f.write(code)
            
            # Try Node.js first, then browser
            try:
                process = await asyncio.create_subprocess_exec(
                    "node", js_file,
                    cwd=self.temp_dir,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, "NODE_PATH": self.temp_dir}
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=input_data.encode()),
                    timeout=timeout
                )
                
                return {
                    "return_code": process.returncode,
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "success": process.returncode == 0,
                    "runtime": "node"
                }
                
            except FileNotFoundError:
                # Fallback to browser execution
                return await self._execute_js_in_browser(code, timeout)
                
        except asyncio.TimeoutError:
            return {
                "error": "JavaScript execution timed out",
                "timeout": timeout,
                "success": False
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    async def _execute_js_in_browser(self, code: str, timeout: int) -> Dict[str, Any]:
        """Execute JavaScript in browser environment"""
        try:
            # Create HTML file with JavaScript
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>JS Execution</title>
            </head>
            <body>
                <div id="output"></div>
                <script>
                    try {{
                        {code}
                        document.getElementById('output').innerHTML = 'Execution completed';
                    }} catch (error) {{
                        document.getElementById('output').innerHTML = 'Error: ' + error.message;
                    }}
                </script>
            </body>
            </html>
            """
            
            html_file = os.path.join(self.temp_dir, "script.html")
            with open(html_file, 'w') as f:
                f.write(html_content)
            
            return {
                "success": True,
                "runtime": "browser",
                "html_file": html_file,
                "output": "Check HTML file for results"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    async def execute_bash_command(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Enhanced bash command execution with relaxed restrictions"""
        try:
            # Enhanced execution with more privileges
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=self.temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True,
                # Allow more capabilities
                env={**os.environ, "PATH": os.environ.get("PATH", "")}
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "return_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "success": process.returncode == 0,
                "command": command
            }
            
        except asyncio.TimeoutError:
            return {
                "error": "Command execution timed out",
                "timeout": timeout,
                "success": False
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    async def execute_generic_code(self, code: str, language: str, timeout: int) -> Dict[str, Any]:
        """Execute code in other languages"""
        try:
            # Create file with appropriate extension
            extensions = {
                "php": "php",
                "ruby": "rb",
                "powershell": "ps1",
                "perl": "pl"
            }
            
            ext = extensions.get(language, "txt")
            file_path = os.path.join(self.temp_dir, f"script.{ext}")
            
            with open(file_path, 'w') as f:
                f.write(code)
            
            # Try to find interpreter
            interpreters = {
                "php": ["php"],
                "ruby": ["ruby"],
                "powershell": ["powershell", "-File"],
                "perl": ["perl"]
            }
            
            interpreter_cmd = interpreters.get(language, ["cat"])
            
            process = await asyncio.create_subprocess_exec(
                *interpreter_cmd + [file_path],
                cwd=self.temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "return_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "success": process.returncode == 0,
                "language": language
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    async def handle_web_code(self, code: str, language: str) -> Dict[str, Any]:
        """Handle HTML/CSS code"""
        try:
            if language == "html":
                filename = "index.html"
            elif language == "css":
                filename = "style.css"
            else:
                raise ValueError(f"Unsupported web language: {language}")
            
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(code)
            
            return {
                "success": True,
                "file_created": filename,
                "file_path": file_path,
                "file_size": len(code),
                "preview_available": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    async def create_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Create a file with given content"""
        try:
            file_path = os.path.join(self.temp_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            return {
                "success": True,
                "file_path": file_path,
                "file_size": len(content)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    async def _analyze_execution_result(self, code: str, result: Dict[str, Any]) -> str:
        """Analyze execution result using ZAI"""
        if not self.zai_client:
            return "Analysis unavailable"
        
        try:
            stdout = result.get("stdout", "")[:500]
            stderr = result.get("stderr", "")[:500]
            
            prompt = f"""Code executed successfully.
Output: {stdout}
Errors: {stderr}

Provide 1-sentence analysis of results."""
            
            return await self.zai_client.generate_text(prompt, temperature=0.2)
        except Exception as e:
            logger.warning(f"Result analysis failed: {str(e)}")
            return "Analysis failed"