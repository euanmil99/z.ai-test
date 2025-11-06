from typing import List, Dict, Any
from ..core import BaseAgent, Task
from loguru import logger
import asyncio

class DataAnalyzerAgent(BaseAgent):
    def __init__(self, agent_id: str = None, name: str = None):
        super().__init__(agent_id, name or "DataAnalyzerAgent")
    
    def get_capabilities(self) -> List[str]:
        return [
            "data_analysis",
            "statistical_analysis",
            "data_visualization",
            "pattern_recognition",
            "data_cleaning",
            "metrics_calculation",
            "trend_analysis"
        ]
    
    def _initialize_tools(self):
        """Initialize data analysis tools"""
        self.tools = {
            "analyze_numbers": self.analyze_numbers,
            "calculate_statistics": self.calculate_statistics,
            "find_patterns": self.find_patterns,
            "clean_data": self.clean_data,
            "generate_report": self.generate_report
        }
    
    async def process_task(self, task: Task) -> Any:
        """Process data analysis task"""
        try:
            parameters = task.parameters
            data = parameters.get("data", [])
            analysis_type = parameters.get("analysis_type", "basic")
            data_source = parameters.get("data_source", "provided")
            
            # Get data
            if data_source == "provided" and not data:
                # Try to extract data from task description or other sources
                data = await self._extract_data_from_context(task)
            
            if not data:
                return {"error": "No data provided for analysis"}
            
            # Perform analysis based on type
            if analysis_type == "statistical":
                result = await self.calculate_statistics(data)
            elif analysis_type == "patterns":
                result = await self.find_patterns(data)
            elif analysis_type == "comprehensive":
                result = await self.comprehensive_analysis(data)
            else:
                result = await self.analyze_numbers(data)
            
            return {
                "analysis_type": analysis_type,
                "data_points": len(data) if isinstance(data, list) else 1,
                "analysis_result": result,
                "summary": self.generate_summary(result)
            }
            
        except Exception as e:
            logger.error(f"Data analysis failed: {str(e)}")
            raise e
    
    async def _extract_data_from_context(self, task: Task) -> List[Any]:
        """Extract data from task context"""
        # This would integrate with other agents or databases
        # For now, return sample data
        return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    async def analyze_numbers(self, data: List[float]) -> Dict[str, Any]:
        """Basic numerical analysis"""
        if not data:
            return {"error": "No data to analyze"}
        
        try:
            # Convert to float if needed
            numeric_data = [float(x) for x in data if isinstance(x, (int, float, str)) and str(x).replace('.', '').isdigit()]
            
            if not numeric_data:
                return {"error": "No numeric data found"}
            
            # Basic statistics
            count = len(numeric_data)
            total = sum(numeric_data)
            mean = total / count
            sorted_data = sorted(numeric_data)
            median = sorted_data[count // 2] if count % 2 == 1 else (sorted_data[count // 2 - 1] + sorted_data[count // 2]) / 2
            
            # Min and max
            min_val = min(numeric_data)
            max_val = max(numeric_data)
            
            # Range and variance
            range_val = max_val - min_val
            variance = sum((x - mean) ** 2 for x in numeric_data) / count
            std_dev = variance ** 0.5
            
            return {
                "count": count,
                "sum": total,
                "mean": mean,
                "median": median,
                "min": min_val,
                "max": max_val,
                "range": range_val,
                "variance": variance,
                "standard_deviation": std_dev,
                "data": numeric_data
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def calculate_statistics(self, data: List[float]) -> Dict[str, Any]:
        """Advanced statistical analysis"""
        basic_stats = await self.analyze_numbers(data)
        
        if "error" in basic_stats:
            return basic_stats
        
        numeric_data = basic_stats["data"]
        
        # Additional statistics
        try:
            # Quartiles
            sorted_data = sorted(numeric_data)
            n = len(sorted_data)
            q1_index = n // 4
            q2_index = n // 2
            q3_index = 3 * n // 4
            
            q1 = sorted_data[q1_index]
            q2 = sorted_data[q2_index]
            q3 = sorted_data[q3_index]
            
            # Interquartile range
            iqr = q3 - q1
            
            # Outliers (using IQR method)
            outliers = [x for x in numeric_data if x < q1 - 1.5 * iqr or x > q3 + 1.5 * iqr]
            
            # Skewness (simplified)
            mean = basic_stats["mean"]
            std_dev = basic_stats["standard_deviation"]
            skewness = sum((x - mean) ** 3 for x in numeric_data) / (n * std_dev ** 3) if std_dev > 0 else 0
            
            return {
                **basic_stats,
                "quartiles": {
                    "q1": q1,
                    "q2": q2,
                    "q3": q3
                },
                "interquartile_range": iqr,
                "outliers": outliers,
                "outlier_count": len(outliers),
                "skewness": skewness,
                "distribution_shape": "positive_skew" if skewness > 0.5 else "negative_skew" if skewness < -0.5 else "normal"
            }
            
        except Exception as e:
            return {**basic_stats, "advanced_stats_error": str(e)}
    
    async def find_patterns(self, data: List[Any]) -> Dict[str, Any]:
        """Find patterns in data"""
        if not data:
            return {"error": "No data to analyze"}
        
        try:
            patterns = {}
            
            # For numeric data
            if all(isinstance(x, (int, float)) for x in data):
                numeric_data = [float(x) for x in data]
                
                # Trend detection
                if len(numeric_data) > 1:
                    increasing = sum(1 for i in range(1, len(numeric_data)) if numeric_data[i] > numeric_data[i-1])
                    decreasing = sum(1 for i in range(1, len(numeric_data)) if numeric_data[i] < numeric_data[i-1])
                    
                    if increasing > decreasing:
                        trend = "increasing"
                    elif decreasing > increasing:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                    
                    patterns["trend"] = trend
                    "trend_strength": abs(increasing - decreasing) / (len(numeric_data) - 1)
                
                # Repeating patterns
                if len(numeric_data) >= 4:
                    # Check for simple repeating patterns
                    for pattern_length in range(2, min(5, len(numeric_data) // 2)):
                        pattern = numeric_data[:pattern_length]
                        repeats = []
                        for i in range(0, len(numeric_data), pattern_length):
                            if i + pattern_length <= len(numeric_data):
                                segment = numeric_data[i:i + pattern_length]
                                if segment == pattern:
                                    repeats.append(i)
                        
                        if len(repeats) > 1:
                            patterns[f"repeating_pattern_{pattern_length}"] = {
                                "pattern": pattern,
                                "occurrences": len(repeats),
                                "positions": repeats
                            }
            
            # For text data
            elif all(isinstance(x, str) for x in data):
                # Frequency analysis
                word_freq = {}
                for item in data:
                    words = item.lower().split()
                    for word in words:
                        word_freq[word] = word_freq.get(word, 0) + 1
                
                if word_freq:
                    most_common = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
                    patterns["most_common_words"] = most_common
                    patterns["unique_words"] = len(word_freq)
                    patterns["total_words"] = sum(word_freq.values())
            
            # General patterns
            patterns["data_type"] = type(data[0]).__name__ if data else "unknown"
            patterns["length"] = len(data)
            patterns["unique_values"] = len(set(data))
            patterns["uniqueness_ratio"] = len(set(data)) / len(data) if data else 0
            
            return {
                "patterns": patterns,
                "data_sample": data[:10]  # First 10 items
            }
            
        except Exception as e:
            return {"error": f"Pattern detection failed: {str(e)}"}
    
    async def clean_data(self, data: List[Any]) -> Dict[str, Any]:
        """Clean and preprocess data"""
        if not data:
            return {"error": "No data to clean"}
        
        try:
            original_count = len(data)
            cleaned = []
            removed = []
            
            for item in data:
                # Remove None values
                if item is None:
                    removed.append({"value": item, "reason": "null_value"})
                    continue
                
                # Remove empty strings
                if isinstance(item, str) and not item.strip():
                    removed.append({"value": item, "reason": "empty_string"})
                    continue
                
                # Convert string numbers to numeric
                if isinstance(item, str) and item.replace('.', '').replace('-', '').isdigit():
                    try:
                        cleaned.append(float(item))
                        continue
                    except ValueError:
                        pass
                
                cleaned.append(item)
            
            # Remove duplicates
            unique_cleaned = []
            duplicates = []
            seen = set()
            
            for item in cleaned:
                # For hashable items
                try:
                    if item not in seen:
                        seen.add(item)
                        unique_cleaned.append(item)
                    else:
                        duplicates.append(item)
                except TypeError:
                    # For unhashable items (like lists), use string representation
                    item_str = str(item)
                    if item_str not in seen:
                        seen.add(item_str)
                        unique_cleaned.append(item)
                    else:
                        duplicates.append(item)
            
            return {
                "original_count": original_count,
                "cleaned_count": len(unique_cleaned),
                "removed_count": len(removed),
                "duplicate_count": len(duplicates),
                "cleaned_data": unique_cleaned,
                "removal_reasons": {reason: len([r for r in removed if r["reason"] == reason]) 
                                  for reason in set(r["reason"] for r in removed)},
                "data_quality_score": len(unique_cleaned) / original_count if original_count > 0 else 0
            }
            
        except Exception as e:
            return {"error": f"Data cleaning failed: {str(e)}"}
    
    async def comprehensive_analysis(self, data: List[Any]) -> Dict[str, Any]:
        """Perform comprehensive data analysis"""
        results = {}
        
        # Basic analysis
        results["basic_analysis"] = await self.analyze_numbers(data)
        
        # Pattern detection
        results["patterns"] = await self.find_patterns(data)
        
        # Data cleaning
        results["cleaning"] = await self.clean_data(data)
        
        # If we have cleaned numeric data, do statistical analysis
        if "cleaned_data" in results["cleaning"]:
            cleaned_data = results["cleaning"]["cleaned_data"]
            if all(isinstance(x, (int, float)) for x in cleaned_data):
                results["statistical_analysis"] = await self.calculate_statistics(cleaned_data)
        
        return results
    
    def generate_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the analysis"""
        if "error" in analysis_result:
            return f"Analysis failed: {analysis_result['error']}"
        
        summary_parts = []
        
        # Basic stats summary
        if "count" in analysis_result:
            count = analysis_result["count"]
            mean = analysis_result.get("mean", 0)
            summary_parts.append(f"Analyzed {count} data points with an average of {mean:.2f}")
        
        # Pattern summary
        if "patterns" in analysis_result:
            patterns = analysis_result["patterns"]
            if isinstance(patterns, dict):
                if "trend" in patterns:
                    summary_parts.append(f"Data shows a {patterns['trend']} trend")
                if "unique_values" in patterns:
                    unique = patterns["unique_values"]
                    total = patterns.get("length", 0)
                    summary_parts.append(f"Found {unique} unique values out of {total} total")
        
        # Cleaning summary
        if "cleaning" in analysis_result:
            cleaning = analysis_result["cleaning"]
            if "data_quality_score" in cleaning:
                quality = cleaning["data_quality_score"]
                summary_parts.append(f"Data quality score: {quality:.2%}")
        
        return ". ".join(summary_parts) if summary_parts else "Analysis completed"
    
    async def generate_report(self, analysis_result: Dict[str, Any]) -> str:
        """Generate a detailed analysis report"""
        report = []
        report.append("# Data Analysis Report\n")
        
        if "error" in analysis_result:
            report.append(f"## Error\n{analysis_result['error']}")
            return "\n".join(report)
        
        # Executive Summary
        report.append("## Executive Summary")
        summary = self.generate_summary(analysis_result)
        report.append(summary + "\n")
        
        # Basic Statistics
        if "count" in analysis_result:
            report.append("## Basic Statistics")
            stats = analysis_result
            report.append(f"- **Count**: {stats.get('count', 'N/A')}")
            report.append(f"- **Mean**: {stats.get('mean', 'N/A'):.2f}")
            report.append(f"- **Median**: {stats.get('median', 'N/A'):.2f}")
            report.append(f"- **Standard Deviation**: {stats.get('standard_deviation', 'N/A'):.2f}")
            report.append(f"- **Min/Max**: {stats.get('min', 'N/A')} / {stats.get('max', 'N/A')}\n")
        
        # Patterns
        if "patterns" in analysis_result:
            report.append("## Patterns Found")
            patterns = analysis_result["patterns"]
            if isinstance(patterns, dict):
                for key, value in patterns.items():
                    report.append(f"- **{key}**: {value}")
            report.append("")
        
        # Data Quality
        if "cleaning" in analysis_result:
            report.append("## Data Quality")
            cleaning = analysis_result["cleaning"]
            report.append(f"- **Original records**: {cleaning.get('original_count', 'N/A')}")
            report.append(f"- **Clean records**: {cleaning.get('cleaned_count', 'N/A')}")
            report.append(f"- **Quality score**: {cleaning.get('data_quality_score', 'N/A'):.2%}\n")
        
        return "\n".join(report)