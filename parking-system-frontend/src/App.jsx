import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Button } from '@/components/ui/button.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';
import { Badge } from '@/components/ui/badge.jsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx';
import { 
  Car, 
  ParkingCircle, 
  Users, 
  CreditCard, 
  BarChart3, 
  Settings,
  LogOut,
  Plus,
  Search,
  Edit,
  Trash2,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign
} from 'lucide-react';
import './App.css';

// Configuração da API
const API_BASE_URL = 'http://localhost:5001/api';

// Serviço de API
class ApiService {
  constructor() {
    this.token = localStorage.getItem('token');
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('token', token);
  }

  removeToken() {
    this.token = null;
    localStorage.removeItem('token');
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.erro || 'Erro na requisição');
      }
      
      return data;
    } catch (error) {
      throw error;
    }
  }

  // Métodos de autenticação
  async login(email, senha) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, senha }),
    });
    this.setToken(data.token);
    return data;
  }

  async logout() {
    await this.request('/auth/logout', { method: 'POST' });
    this.removeToken();
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  // Métodos para vagas
  async getVagas() {
    return this.request('/vagas/');
  }

  async getOcupacao() {
    return this.request('/vagas/ocupacao');
  }

  // Métodos para estacionamentos
  async getEstacionamentos() {
    return this.request('/estacionamentos/');
  }

  async getEstacionamentosAtivos() {
    return this.request('/estacionamentos/ativos');
  }

  async criarEstacionamento(data) {
    return this.request('/estacionamentos/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async encerrarEstacionamento(id) {
    return this.request(`/estacionamentos/${id}/encerrar`, {
      method: 'POST',
    });
  }

  // Métodos para veículos
  async getVeiculos() {
    return this.request('/veiculos/');
  }

  async criarVeiculo(data) {
    return this.request('/veiculos/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async buscarVeiculoPorPlaca(placa) {
    return this.request(`/veiculos/placa/${placa}`);
  }

  // Métodos para clientes
  async getClientes() {
    return this.request('/clientes/');
  }

  async criarCliente(data) {
    return this.request('/clientes/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Métodos para pagamentos
  async calcularPagamento(estacionamentoId) {
    return this.request(`/pagamentos/calcular/${estacionamentoId}`);
  }

  async processarPagamento(data) {
    return this.request('/pagamentos/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getResumoFaturamento() {
    return this.request('/pagamentos/resumo');
  }
}

const api = new ApiService();

// Componente de Login
function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await api.login(email, senha);
      onLogin(data.usuario);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
            <ParkingCircle className="w-6 h-6 text-white" />
          </div>
          <CardTitle className="text-2xl">Simplifica Parking</CardTitle>
          <CardDescription>Faça login para acessar o sistema</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="senha">Senha</Label>
              <Input
                id="senha"
                type="password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                placeholder="Sua senha"
                required
              />
            </div>
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Entrando...' : 'Entrar'}
            </Button>
          </form>
          <div className="mt-4 text-sm text-gray-600 text-center">
            <p>Usuário padrão: admin@estacionamento.com</p>
            <p>Senha: admin123</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Componente do Dashboard
function Dashboard() {
  const [ocupacao, setOcupacao] = useState(null);
  const [estacionamentosAtivos, setEstacionamentosAtivos] = useState([]);
  const [resumoFaturamento, setResumoFaturamento] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [ocupacaoData, estacionamentosData, faturamentoData] = await Promise.all([
        api.getOcupacao(),
        api.getEstacionamentosAtivos(),
        api.getResumoFaturamento()
      ]);
      
      setOcupacao(ocupacaoData);
      setEstacionamentosAtivos(estacionamentosData);
      setResumoFaturamento(faturamentoData);
    } catch (error) {
      console.error('Erro ao carregar dados do dashboard:', error);
    }
  };

  if (!ocupacao) {
    return <div className="p-6">Carregando...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      
      {/* Cards de estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total de Vagas</CardTitle>
            <ParkingCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{ocupacao.total_vagas}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Vagas Ocupadas</CardTitle>
            <Car className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{ocupacao.vagas_ocupadas}</div>
            <p className="text-xs text-muted-foreground">
              {ocupacao.percentual_ocupacao}% de ocupação
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Vagas Disponíveis</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{ocupacao.vagas_disponiveis}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Faturamento Hoje</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              R$ {resumoFaturamento?.valor_total_arrecadado?.toFixed(2) || '0,00'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Estacionamentos ativos */}
      <Card>
        <CardHeader>
          <CardTitle>Estacionamentos Ativos</CardTitle>
          <CardDescription>
            Veículos atualmente estacionados ({estacionamentosAtivos.length})
          </CardDescription>
        </CardHeader>
        <CardContent>
          {estacionamentosAtivos.length === 0 ? (
            <p className="text-muted-foreground">Nenhum veículo estacionado no momento.</p>
          ) : (
            <div className="space-y-2">
              {estacionamentosAtivos.slice(0, 5).map((estacionamento) => (
                <div key={estacionamento.id} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <span className="font-medium">Vaga: {estacionamento.vaga_id}</span>
                    <span className="text-sm text-muted-foreground ml-2">
                      Entrada: {new Date(estacionamento.entrada_em).toLocaleString()}
                    </span>
                  </div>
                  <Badge variant="secondary">Ativo</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Componente de Entrada de Veículos
function EntradaVeiculos() {
  const [placa, setPlaca] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  const handleEntrada = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      // Primeiro, buscar o veículo pela placa
      let veiculo;
      try {
        veiculo = await api.buscarVeiculoPorPlaca(placa);
      } catch (error) {
        // Se veículo não existe, criar um novo cliente e veículo
        const novoCliente = await api.criarCliente({
          nome: `Cliente - ${placa}`,
        });
        
        veiculo = await api.criarVeiculo({
          cliente_id: novoCliente.id,
          placa: placa,
          tipo_veiculo: 'pequeno', // Padrão
        });
      }

      // Criar estacionamento
      const estacionamento = await api.criarEstacionamento({
        veiculo_id: veiculo.id,
      });

      setMessage(`Veículo ${placa} registrado com sucesso! Vaga: ${estacionamento.vaga_id}`);
      setMessageType('success');
      setPlaca('');
    } catch (error) {
      setMessage(error.message);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Entrada de Veículos</h1>
      
      <Card className="max-w-md">
        <CardHeader>
          <CardTitle>Registrar Entrada</CardTitle>
          <CardDescription>Digite a placa do veículo para registrar a entrada</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleEntrada} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="placa">Placa do Veículo</Label>
              <Input
                id="placa"
                value={placa}
                onChange={(e) => setPlaca(e.target.value.toUpperCase())}
                placeholder="ABC-1234"
                required
              />
            </div>
            
            {message && (
              <Alert variant={messageType === 'error' ? 'destructive' : 'default'}>
                <AlertDescription>{message}</AlertDescription>
              </Alert>
            )}
            
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Registrando...' : 'Registrar Entrada'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

// Componente de Saída de Veículos
function SaidaVeiculos() {
  const [estacionamentosAtivos, setEstacionamentosAtivos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadEstacionamentosAtivos();
  }, []);

  const loadEstacionamentosAtivos = async () => {
    try {
      const data = await api.getEstacionamentosAtivos();
      setEstacionamentosAtivos(data);
    } catch (error) {
      console.error('Erro ao carregar estacionamentos ativos:', error);
    }
  };

  const handleSaida = async (estacionamentoId) => {
    setLoading(true);
    setMessage('');

    try {
      await api.encerrarEstacionamento(estacionamentoId);
      setMessage('Saída registrada com sucesso!');
      loadEstacionamentosAtivos(); // Recarregar lista
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Saída de Veículos</h1>
      
      {message && (
        <Alert>
          <AlertDescription>{message}</AlertDescription>
        </Alert>
      )}
      
      <Card>
        <CardHeader>
          <CardTitle>Veículos Estacionados</CardTitle>
          <CardDescription>
            Clique em "Registrar Saída" para finalizar o estacionamento
          </CardDescription>
        </CardHeader>
        <CardContent>
          {estacionamentosAtivos.length === 0 ? (
            <p className="text-muted-foreground">Nenhum veículo estacionado no momento.</p>
          ) : (
            <div className="space-y-4">
              {estacionamentosAtivos.map((estacionamento) => (
                <div key={estacionamento.id} className="flex items-center justify-between p-4 border rounded">
                  <div>
                    <p className="font-medium">Vaga: {estacionamento.vaga_id}</p>
                    <p className="text-sm text-muted-foreground">
                      Entrada: {new Date(estacionamento.entrada_em).toLocaleString()}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      QR Code: {estacionamento.tiquete_qr_code}
                    </p>
                  </div>
                  <Button 
                    onClick={() => handleSaida(estacionamento.id)}
                    disabled={loading}
                  >
                    Registrar Saída
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Componente principal da aplicação
function MainApp({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('dashboard');

  const handleLogout = async () => {
    try {
      await api.logout();
      onLogout();
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
      onLogout(); // Fazer logout mesmo se houver erro
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <ParkingCircle className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-xl font-semibold">Simplifica Parking</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">Olá, {user.nome}</span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" />
                Sair
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="dashboard" className="flex items-center">
                <BarChart3 className="h-4 w-4 mr-2" />
                Dashboard
              </TabsTrigger>
              <TabsTrigger value="entrada" className="flex items-center">
                <Plus className="h-4 w-4 mr-2" />
                Entrada
              </TabsTrigger>
              <TabsTrigger value="saida" className="flex items-center">
                <XCircle className="h-4 w-4 mr-2" />
                Saída
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </nav>

      {/* Content */}
      <main>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsContent value="dashboard">
            <Dashboard />
          </TabsContent>
          <TabsContent value="entrada">
            <EntradaVeiculos />
          </TabsContent>
          <TabsContent value="saida">
            <SaidaVeiculos />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

// Componente principal
function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const userData = await api.getCurrentUser();
        setUser(userData);
      } catch (error) {
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  };

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <ParkingCircle className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-spin" />
          <p>Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        {user ? (
          <MainApp user={user} onLogout={handleLogout} />
        ) : (
          <LoginPage onLogin={handleLogin} />
        )}
      </div>
    </Router>
  );
}

export default App;

