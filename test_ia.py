# rate_limit_checker.py
import os
import requests
import time
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class OpenRouterDiagnostic:
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        
    def check_environment(self):
        """Verifica las variables de entorno críticas"""
        print("🔍 CHECKING ENVIRONMENT VARIABLES")
        print("=" * 50)
        
        env_vars = {
            "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY"),
            "OPENROUTER_REFRESH_TOKEN": os.environ.get("OPENROUTER_REFRESH_TOKEN"),
            "ORACLE_URL": os.environ.get("ORACLE_URL"),
            "ORACLE_USER": os.environ.get("ORACLE_USER"),
            "ORACLE_PASSWORD": os.environ.get("ORACLE_PASSWORD"),
        }
        
        for key, value in env_vars.items():
            status = "✅ SET" if value else "❌ MISSING"
            display_value = value[:20] + "..." if value and len(value) > 20 else value
            print(f"{key}: {status}")
            if value:
                print(f"   Value: {display_value}")
        print()
    
    def check_api_key_validity(self):
        """Verifica si la API key es válida"""
        print("🔑 CHECKING API KEY VALIDITY")
        print("=" * 50)
        
        if not self.api_key:
            print("❌ No API key found")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/auth/key",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API Key is valid")
                print(f"   Key ID: {data.get('id', 'N/A')}")
                print(f"   Created: {data.get('created_at', 'N/A')}")
                return True
            else:
                print(f"❌ API Key validation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error validating API key: {e}")
            return False
        print()
    
    def check_rate_limits(self):
        """Verifica los límites de tasa actuales"""
        print("📊 CHECKING RATE LIMITS")
        print("=" * 50)
        
        if not self.api_key:
            print("❌ No API key available for rate limit check")
            return
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Hacer una pequeña solicitud de prueba
            test_payload = {
                "model": "deepseek/deepseek-r1-0528:free",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 100
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=30
            )
            response_time = time.time() - start_time
            
            print(f"Response Time: {response_time:.2f}s")
            print(f"Status Code: {response.status_code}")
            
            # Verificar headers de rate limiting
            rate_headers = {
                "x-ratelimit-limit-requests": "Request Limit",
                "x-ratelimit-remaining-requests": "Remaining Requests", 
                "x-ratelimit-reset-requests": "Reset Time",
                "x-ratelimit-limit-tokens": "Token Limit",
                "x-ratelimit-remaining-tokens": "Remaining Tokens"
            }
            
            print("\nRate Limit Headers:")
            for header, description in rate_headers.items():
                value = response.headers.get(header, "Not Available")
                print(f"   {description}: {value}")
            
            if response.status_code == 429:
                print("\n🚨 RATE LIMIT EXCEEDED!")
                retry_after = response.headers.get('retry-after', 'Unknown')
                print(f"   Retry after: {retry_after} seconds")
            
            print(f"\nResponse Headers Sample:")
            for header, value in list(response.headers.items())[:10]:
                print(f"   {header}: {value}")
                
        except requests.exceptions.Timeout:
            print("❌ Request timeout - server may be overloaded")
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - check internet connection")
        except Exception as e:
            print(f"❌ Error checking rate limits: {e}")
        print()
    
    def test_throughput(self, num_requests=3, delay=2):
        """Test de throughput para simular uso real"""
        print("🚀 PERFORMING THROUGHPUT TEST")
        print("=" * 50)
        print(f"Requests: {num_requests}, Delay: {delay}s")
        
        if not self.api_key:
            print("❌ No API key available for test")
            return
        
        successes = 0
        failures = 0
        response_times = []
        
        for i in range(num_requests):
            try:
                print(f"\nRequest {i+1}/{num_requests}:")
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                test_payload = {
                    "model": "deepseek/deepseek-r1-0528:free",
                    "messages": [{"role": "user", "content": f"Test message {i+1}"}],
                    "max_tokens": 5
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=test_payload,
                    timeout=30
                )
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                print(f"   Time: {response_time:.2f}s")
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    successes += 1
                    print("   Result: ✅ Success")
                elif response.status_code == 429:
                    failures += 1
                    print("   Result: 🚨 Rate Limited")
                    retry_after = response.headers.get('retry-after', 'Unknown')
                    print(f"   Retry after: {retry_after}s")
                else:
                    failures += 1
                    print(f"   Result: ❌ Failed - {response.text[:100]}")
                
                if i < num_requests - 1:
                    print(f"   Waiting {delay}s...")
                    time.sleep(delay)
                    
            except Exception as e:
                failures += 1
                print(f"   Result: ❌ Exception - {e}")
        
        # Resumen del test
        print(f"\n📈 THROUGHPUT TEST SUMMARY:")
        print(f"   Successful: {successes}/{num_requests}")
        print(f"   Failed: {failures}/{num_requests}")
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            print(f"   Avg Response Time: {avg_time:.2f}s")
            print(f"   Min-Max Time: {min_time:.2f}s-{max_time:.2f}s")
        print()
    
    def check_model_availability(self):
        """Verifica disponibilidad de modelos"""
        print("🤖 CHECKING MODEL AVAILABILITY")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/models", timeout=10)
            
            if response.status_code == 200:
                models = response.json().get('data', [])
                deepseek_models = [m for m in models if 'deepseek' in m['id'].lower()]
                
                print(f"Total models available: {len(models)}")
                print(f"DeepSeek models: {len(deepseek_models)}")
                
                for model in deepseek_models[:3]:  # Mostrar primeros 3
                    print(f"   📋 {model['id']}")
                    print(f"      Context: {model.get('context_length', 'N/A')} tokens")
                    print(f"      Description: {model.get('description', 'N/A')[:100]}...")
            else:
                print(f"❌ Error fetching models: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error checking models: {e}")
        print()
    
    def generate_recommendations(self):
        """Genera recomendaciones basadas en los checks"""
        print("💡 RECOMMENDATIONS")
        print("=" * 50)
        
        recommendations = []
        
        # Verificar delay entre requests
        if not hasattr(self, 'test_results'):
            recommendations.append("• Run throughput test first for specific recommendations")
        else:
            recommendations.append("• Maintain at least 2-3 seconds between requests")
            recommendations.append("• Implement exponential backoff for 429 errors")
            recommendations.append("• Cache responses when possible to reduce API calls")
            recommendations.append("• Use streaming for long responses to save tokens")
        
        # Recomendaciones generales
        if not os.environ.get("OPENROUTER_API_KEY"):
            recommendations.append("• Set OPENROUTER_API_KEY environment variable")
        
        recommendations.append("• Monitor rate limit headers in each response")
        recommendations.append("• Consider upgrading plan if limits are too restrictive")
        recommendations.append("• Implement request queuing for high-volume applications")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        print()

def main():
    """Función principal"""
    print("🚀 OPENROUTER DIAGNOSTIC TOOL")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    diagnostic = OpenRouterDiagnostic()
    
    # Ejecutar todas las verificaciones
    diagnostic.check_environment()
    diagnostic.check_api_key_validity()
    diagnostic.check_rate_limits()
    diagnostic.check_model_availability()
    
    # Preguntar si ejecutar test de throughput
    try:
        run_test = input("Run throughput test? (y/n): ").lower().strip()
        if run_test in ['y', 'yes']:
            diagnostic.test_throughput(num_requests=3, delay=2)
    except:
        print("Skipping throughput test")
    
    diagnostic.generate_recommendations()
    
    print("🎯 DIAGNOSTIC COMPLETE")
    print("Check the recommendations above to optimize your OpenRouter usage.")

if __name__ == "__main__":
    main()