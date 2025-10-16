"""
BRI Performance Evaluation Framework
Tests BRI's ability to answer questions about video content with 50 test cases.
"""

import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from services.agent import GroqAgent
from services.memory import Memory
from storage.database import Database


@dataclass
class EvalTestCase:
    """Single evaluation test case."""
    id: int
    video_id: str
    question: str
    expected_keywords: List[str]  # Keywords that should appear in response
    category: str  # "scene", "object", "audio", "timestamp", "general"
    difficulty: str  # "easy", "medium", "hard"


@dataclass
class EvalResult:
    """Result of a single evaluation."""
    test_id: int
    question: str
    response: str
    keywords_found: List[str]
    keywords_missing: List[str]
    score: float  # 0.0 to 1.0
    response_time: float
    category: str
    difficulty: str
    passed: bool


class BRIEvaluator:
    """Evaluates BRI's performance on video question answering."""
    
    def __init__(self):
        self.agent = GroqAgent()
        self.results: List[EvalResult] = []
    
    def get_test_cases(self) -> List[EvalTestCase]:
        """Generate 50 test cases across different categories."""
        test_cases = []
        
        # Scene Description Tests (10 cases)
        scene_tests = [
            EvalTestCase(1, "test_video", "What's happening in the video?", 
                        ["scene", "showing", "video"], "scene", "easy"),
            EvalTestCase(2, "test_video", "Describe what you see at the beginning",
                        ["beginning", "start", "first"], "scene", "easy"),
            EvalTestCase(3, "test_video", "What's the main action in this video?",
                        ["action", "main", "doing"], "scene", "medium"),
            EvalTestCase(4, "test_video", "Describe the setting or environment",
                        ["setting", "environment", "location"], "scene", "medium"),
            EvalTestCase(5, "test_video", "What changes happen throughout the video?",
                        ["change", "throughout", "different"], "scene", "hard"),
            EvalTestCase(6, "test_video", "What's the mood or atmosphere?",
                        ["mood", "atmosphere", "feel"], "scene", "medium"),
            EvalTestCase(7, "test_video", "Describe the lighting and colors",
                        ["lighting", "color", "bright", "dark"], "scene", "medium"),
            EvalTestCase(8, "test_video", "What's in the background?",
                        ["background", "behind", "back"], "scene", "easy"),
            EvalTestCase(9, "test_video", "What's in the foreground?",
                        ["foreground", "front", "close"], "scene", "easy"),
            EvalTestCase(10, "test_video", "How would you summarize this video?",
                        ["summary", "overall", "about"], "scene", "medium"),
        ]
        
        # Object Detection Tests (15 cases)
        object_tests = [
            EvalTestCase(11, "test_video", "What objects can you see?",
                        ["object", "see", "visible"], "object", "easy"),
            EvalTestCase(12, "test_video", "Are there any people in the video?",
                        ["people", "person", "human"], "object", "easy"),
            EvalTestCase(13, "test_video", "How many people appear?",
                        ["how many", "count", "number"], "object", "medium"),
            EvalTestCase(14, "test_video", "What are people wearing?",
                        ["wearing", "clothes", "dressed"], "object", "medium"),
            EvalTestCase(15, "test_video", "Are there any vehicles?",
                        ["vehicle", "car", "truck"], "object", "easy"),
            EvalTestCase(16, "test_video", "What furniture is visible?",
                        ["furniture", "chair", "table"], "object", "easy"),
            EvalTestCase(17, "test_video", "Are there any animals?",
                        ["animal", "dog", "cat", "bird"], "object", "easy"),
            EvalTestCase(18, "test_video", "What electronic devices can you see?",
                        ["electronic", "device", "phone", "computer"], "object", "medium"),
            EvalTestCase(19, "test_video", "Is there any text or signage?",
                        ["text", "sign", "writing"], "object", "medium"),
            EvalTestCase(20, "test_video", "What's the largest object?",
                        ["largest", "biggest", "main"], "object", "medium"),
            EvalTestCase(21, "test_video", "What colors are prominent?",
                        ["color", "prominent", "main"], "object", "easy"),
            EvalTestCase(22, "test_video", "Are there any tools or equipment?",
                        ["tool", "equipment", "device"], "object", "medium"),
            EvalTestCase(23, "test_video", "What's on the walls?",
                        ["wall", "hanging", "mounted"], "object", "easy"),
            EvalTestCase(24, "test_video", "Are there any plants or nature elements?",
                        ["plant", "nature", "tree", "flower"], "object", "easy"),
            EvalTestCase(25, "test_video", "What objects are moving?",
                        ["moving", "motion", "dynamic"], "object", "hard"),
        ]
        
        # Audio/Transcript Tests (10 cases)
        audio_tests = [
            EvalTestCase(26, "test_video", "What is being said in the video?",
                        ["said", "speaking", "audio"], "audio", "easy"),
            EvalTestCase(27, "test_video", "Can you transcribe what you hear?",
                        ["transcribe", "hear", "audio"], "audio", "medium"),
            EvalTestCase(28, "test_video", "What's the first thing said?",
                        ["first", "beginning", "start"], "audio", "medium"),
            EvalTestCase(29, "test_video", "What's the last thing mentioned?",
                        ["last", "end", "final"], "audio", "medium"),
            EvalTestCase(30, "test_video", "Is there any background music?",
                        ["music", "background", "sound"], "audio", "easy"),
            EvalTestCase(31, "test_video", "What's the tone of the speaker?",
                        ["tone", "voice", "speaking"], "audio", "medium"),
            EvalTestCase(32, "test_video", "Are there multiple speakers?",
                        ["multiple", "speakers", "people"], "audio", "medium"),
            EvalTestCase(33, "test_video", "What topics are discussed?",
                        ["topic", "discuss", "about"], "audio", "medium"),
            EvalTestCase(34, "test_video", "Is there any laughter or emotion?",
                        ["laughter", "emotion", "feeling"], "audio", "hard"),
            EvalTestCase(35, "test_video", "What keywords are repeated?",
                        ["keyword", "repeated", "often"], "audio", "hard"),
        ]
        
        # Timestamp/Temporal Tests (8 cases)
        timestamp_tests = [
            EvalTestCase(36, "test_video", "What happens at the beginning?",
                        ["beginning", "start", "first"], "timestamp", "easy"),
            EvalTestCase(37, "test_video", "What happens at the end?",
                        ["end", "final", "last"], "timestamp", "easy"),
            EvalTestCase(38, "test_video", "What happens in the middle?",
                        ["middle", "halfway", "center"], "timestamp", "medium"),
            EvalTestCase(39, "test_video", "When does the main action occur?",
                        ["when", "time", "moment"], "timestamp", "medium"),
            EvalTestCase(40, "test_video", "What's the sequence of events?",
                        ["sequence", "order", "first", "then"], "timestamp", "hard"),
            EvalTestCase(41, "test_video", "How long does the main scene last?",
                        ["how long", "duration", "time"], "timestamp", "hard"),
            EvalTestCase(42, "test_video", "What changes over time?",
                        ["change", "over time", "throughout"], "timestamp", "medium"),
            EvalTestCase(43, "test_video", "Is there a climax or key moment?",
                        ["climax", "key", "important"], "timestamp", "medium"),
        ]
        
        # General/Context Tests (7 cases)
        general_tests = [
            EvalTestCase(44, "test_video", "What's the purpose of this video?",
                        ["purpose", "goal", "why"], "general", "medium"),
            EvalTestCase(45, "test_video", "Who is the intended audience?",
                        ["audience", "for", "intended"], "general", "hard"),
            EvalTestCase(46, "test_video", "What's the overall message?",
                        ["message", "point", "meaning"], "general", "hard"),
            EvalTestCase(47, "test_video", "Is this educational or entertainment?",
                        ["educational", "entertainment", "type"], "general", "medium"),
            EvalTestCase(48, "test_video", "What genre or category is this?",
                        ["genre", "category", "type"], "general", "medium"),
            EvalTestCase(49, "test_video", "What emotions does it evoke?",
                        ["emotion", "feel", "evoke"], "general", "hard"),
            EvalTestCase(50, "test_video", "Would you recommend this video?",
                        ["recommend", "good", "worth"], "general", "easy"),
        ]
        
        test_cases.extend(scene_tests)
        test_cases.extend(object_tests)
        test_cases.extend(audio_tests)
        test_cases.extend(timestamp_tests)
        test_cases.extend(general_tests)
        
        return test_cases
    
    async def evaluate_single(self, test_case: EvalTestCase) -> EvalResult:
        """Evaluate a single test case."""
        start_time = time.time()
        
        try:
            # Get response from BRI
            response = await self.agent.chat(test_case.question, test_case.video_id)
            response_text = response.message.lower()
            
            # Check which keywords were found
            keywords_found = []
            keywords_missing = []
            
            for keyword in test_case.expected_keywords:
                if keyword.lower() in response_text:
                    keywords_found.append(keyword)
                else:
                    keywords_missing.append(keyword)
            
            # Calculate score
            score = len(keywords_found) / len(test_case.expected_keywords) if test_case.expected_keywords else 0.0
            passed = score >= 0.5  # Pass if at least 50% of keywords found
            
            response_time = time.time() - start_time
            
            return EvalResult(
                test_id=test_case.id,
                question=test_case.question,
                response=response.message,
                keywords_found=keywords_found,
                keywords_missing=keywords_missing,
                score=score,
                response_time=response_time,
                category=test_case.category,
                difficulty=test_case.difficulty,
                passed=passed
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return EvalResult(
                test_id=test_case.id,
                question=test_case.question,
                response=f"ERROR: {str(e)}",
                keywords_found=[],
                keywords_missing=test_case.expected_keywords,
                score=0.0,
                response_time=response_time,
                category=test_case.category,
                difficulty=test_case.difficulty,
                passed=False
            )
    
    async def run_evaluation(self, video_id: str) -> Dict[str, Any]:
        """Run full evaluation suite."""
        print("Starting BRI Performance Evaluation...")
        print(f"Video ID: {video_id}")
        print("=" * 60)
        
        test_cases = self.get_test_cases()
        # Update video_id for all test cases
        for tc in test_cases:
            tc.video_id = video_id
        
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/50] Testing: {test_case.question[:50]}...")
            result = await self.evaluate_single(test_case)
            results.append(result)
            
            status = "PASS" if result.passed else "FAIL"
            print(f"  {status} | Score: {result.score:.2f} | Time: {result.response_time:.2f}s")
        
        self.results = results
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive evaluation report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        total_score = sum(r.score for r in self.results) / total_tests if total_tests > 0 else 0
        avg_response_time = sum(r.response_time for r in self.results) / total_tests if total_tests > 0 else 0
        
        # Category breakdown
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {"total": 0, "passed": 0, "score": 0}
            categories[result.category]["total"] += 1
            if result.passed:
                categories[result.category]["passed"] += 1
            categories[result.category]["score"] += result.score
        
        for cat in categories:
            categories[cat]["avg_score"] = categories[cat]["score"] / categories[cat]["total"]
            categories[cat]["pass_rate"] = categories[cat]["passed"] / categories[cat]["total"]
        
        # Difficulty breakdown
        difficulties = {}
        for result in self.results:
            if result.difficulty not in difficulties:
                difficulties[result.difficulty] = {"total": 0, "passed": 0, "score": 0}
            difficulties[result.difficulty]["total"] += 1
            if result.passed:
                difficulties[result.difficulty]["passed"] += 1
            difficulties[result.difficulty]["score"] += result.score
        
        for diff in difficulties:
            difficulties[diff]["avg_score"] = difficulties[diff]["score"] / difficulties[diff]["total"]
            difficulties[diff]["pass_rate"] = difficulties[diff]["passed"] / difficulties[diff]["total"]
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "average_score": total_score,
                "average_response_time": avg_response_time
            },
            "by_category": categories,
            "by_difficulty": difficulties,
            "detailed_results": [asdict(r) for r in self.results]
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = "eval_report.json"):
        """Save evaluation report to file."""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to {filename}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Print evaluation summary."""
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        
        summary = report["summary"]
        print(f"\nPassed: {summary['passed']}/{summary['total_tests']} ({summary['pass_rate']:.1%})")
        print(f"Average Score: {summary['average_score']:.2f}")
        print(f"Average Response Time: {summary['average_response_time']:.2f}s")
        
        print("\nBy Category:")
        for cat, stats in report["by_category"].items():
            print(f"  {cat.upper()}: {stats['passed']}/{stats['total']} passed ({stats['pass_rate']:.1%}) | Avg Score: {stats['avg_score']:.2f}")
        
        print("\nBy Difficulty:")
        for diff, stats in report["by_difficulty"].items():
            print(f"  {diff.upper()}: {stats['passed']}/{stats['total']} passed ({stats['pass_rate']:.1%}) | Avg Score: {stats['avg_score']:.2f}")


async def main():
    """Main evaluation entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tests/eval_bri_performance.py <video_id>")
        print("\nExample: python tests/eval_bri_performance.py 75befeed-4502-492c-a62d-d30d1852ef9a")
        sys.exit(1)
    
    video_id = sys.argv[1]
    
    evaluator = BRIEvaluator()
    report = await evaluator.run_evaluation(video_id)
    
    evaluator.print_summary(report)
    evaluator.save_report(report, f"eval_report_{video_id[:8]}.json")
    
    print("\nEvaluation complete!")


if __name__ == "__main__":
    asyncio.run(main())
