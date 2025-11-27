import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';

type UserRole = 'buyer' | 'seller';

interface Deal {
  id: string;
  type: 'buy' | 'sell';
  amount: number;
  price: number;
  currency: string;
  counterparty: string;
  status: 'pending' | 'escrow' | 'completed' | 'cancelled';
  date: string;
}

interface Offer {
  id: string;
  seller: string;
  price: number;
  minAmount: number;
  maxAmount: number;
  currency: string;
  rating: number;
  deals: number;
}

const Index = () => {
  const [userRole, setUserRole] = useState<UserRole>('buyer');
  const [activeTab, setActiveTab] = useState('profile');

  const stats = {
    balance: 1250.50,
    totalBought: 15420,
    totalSold: 8300,
    completedDeals: 47
  };

  const mockOffers: Offer[] = [
    { id: '1', seller: 'CryptoKing', price: 95.50, minAmount: 100, maxAmount: 5000, currency: 'USDT', rating: 4.9, deals: 1250 },
    { id: '2', seller: 'TraderPro', price: 95.30, minAmount: 50, maxAmount: 3000, currency: 'USDT', rating: 4.8, deals: 890 },
    { id: '3', seller: 'BitMaster', price: 95.75, minAmount: 200, maxAmount: 10000, currency: 'USDT', rating: 5.0, deals: 2100 },
  ];

  const mockDeals: Deal[] = [
    { id: 'D1', type: 'buy', amount: 500, price: 95.50, currency: 'USDT', counterparty: 'CryptoKing', status: 'escrow', date: '2025-11-27 14:30' },
    { id: 'D2', type: 'sell', amount: 1000, price: 96.00, currency: 'USDT', counterparty: 'TraderPro', status: 'pending', date: '2025-11-27 12:15' },
    { id: 'D3', type: 'buy', amount: 750, price: 95.30, currency: 'USDT', counterparty: 'BitMaster', status: 'completed', date: '2025-11-26 18:45' },
  ];

  const handleRoleSwitch = (checked: boolean) => {
    setUserRole(checked ? 'seller' : 'buyer');
    toast.success(`Режим ${checked ? 'продавца' : 'покупателя'} активирован`);
  };

  const getStatusColor = (status: Deal['status']) => {
    switch (status) {
      case 'completed': return 'success-bg';
      case 'escrow': return 'bg-primary';
      case 'pending': return 'bg-yellow-600';
      case 'cancelled': return 'bg-destructive';
    }
  };

  const getStatusText = (status: Deal['status']) => {
    switch (status) {
      case 'completed': return 'Завершена';
      case 'escrow': return 'Эскроу';
      case 'pending': return 'Ожидание';
      case 'cancelled': return 'Отменена';
    }
  };

  return (
    <div className="min-h-screen bg-background p-4 md:p-6">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl font-bold text-foreground">P2P Exchange</h1>
            <Avatar className="h-10 w-10 bg-primary">
              <AvatarFallback className="text-primary-foreground">ME</AvatarFallback>
            </Avatar>
          </div>
          <p className="text-muted-foreground">Безопасная торговля криптовалютой</p>
        </header>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-secondary">
            <TabsTrigger value="profile">Профиль</TabsTrigger>
            <TabsTrigger value="trade">{userRole === 'buyer' ? 'Купить' : 'Продать'}</TabsTrigger>
            <TabsTrigger value="deals">Сделки</TabsTrigger>
          </TabsList>

          <TabsContent value="profile" className="space-y-6 animate-fade-in">
            <Card className="p-6 bg-card border-border">
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold mb-1">Режим работы</h2>
                    <p className="text-sm text-muted-foreground">
                      {userRole === 'buyer' ? 'Покупатель валюты' : 'Продавец валюты'}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Label htmlFor="role-switch" className="text-sm">
                      {userRole === 'buyer' ? 'Покупатель' : 'Продавец'}
                    </Label>
                    <Switch
                      id="role-switch"
                      checked={userRole === 'seller'}
                      onCheckedChange={handleRoleSwitch}
                    />
                  </div>
                </div>

                <Separator />

                <div>
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Icon name="Wallet" size={20} />
                    Баланс
                  </h3>
                  <div className="bg-secondary rounded-lg p-6 mb-4">
                    <div className="text-4xl font-bold mb-2">${stats.balance.toFixed(2)}</div>
                    <div className="text-sm text-muted-foreground">Доступно для торговли</div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <Button className="w-full bg-primary hover:bg-primary/90" onClick={() => toast.info('Функция пополнения в разработке')}>
                      <Icon name="Plus" size={18} className="mr-2" />
                      Пополнить
                    </Button>
                    <Button variant="outline" className="w-full" onClick={() => toast.info('Функция вывода в разработке')}>
                      <Icon name="ArrowUp" size={18} className="mr-2" />
                      Вывести
                    </Button>
                  </div>
                </div>

                <Separator />

                <div>
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Icon name="BarChart3" size={20} />
                    Статистика
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="bg-secondary rounded-lg p-4">
                      <div className="text-2xl font-bold success-text">${stats.totalBought.toLocaleString()}</div>
                      <div className="text-sm text-muted-foreground">Куплено</div>
                    </div>
                    <div className="bg-secondary rounded-lg p-4">
                      <div className="text-2xl font-bold text-blue-500">${stats.totalSold.toLocaleString()}</div>
                      <div className="text-sm text-muted-foreground">Продано</div>
                    </div>
                    <div className="bg-secondary rounded-lg p-4 col-span-2 md:col-span-1">
                      <div className="text-2xl font-bold text-primary">{stats.completedDeals}</div>
                      <div className="text-sm text-muted-foreground">Сделок завершено</div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="trade" className="animate-fade-in">
            {userRole === 'buyer' ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-semibold">Купить криптовалюту</h2>
                  <Badge variant="outline" className="text-sm">
                    <Icon name="TrendingDown" size={14} className="mr-1" />
                    Лучшие предложения
                  </Badge>
                </div>
                {mockOffers.map((offer) => (
                  <Card key={offer.id} className="p-6 bg-card border-border hover:border-primary transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <Avatar className="h-10 w-10 bg-primary/20">
                            <AvatarFallback className="text-primary">{offer.seller[0]}</AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-semibold">{offer.seller}</div>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Icon name="Star" size={14} className="text-yellow-500 fill-yellow-500" />
                              <span>{offer.rating}</span>
                              <span>•</span>
                              <span>{offer.deals} сделок</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-6 text-sm">
                          <div>
                            <span className="text-muted-foreground">Цена: </span>
                            <span className="font-semibold">${offer.price}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Лимит: </span>
                            <span className="font-semibold">${offer.minAmount} - ${offer.maxAmount}</span>
                          </div>
                          <Badge variant="secondary">{offer.currency}</Badge>
                        </div>
                      </div>
                      <Button className="bg-primary hover:bg-primary/90" onClick={() => toast.success('Сделка инициирована')}>
                        Купить
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="p-8 bg-card border-border">
                <div className="max-w-md mx-auto space-y-6">
                  <div className="text-center mb-6">
                    <Icon name="Tag" size={48} className="mx-auto mb-4 text-primary" />
                    <h2 className="text-2xl font-semibold mb-2">Создать объявление</h2>
                    <p className="text-muted-foreground">Укажите условия продажи криптовалюты</p>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="price">Цена за единицу ($)</Label>
                      <Input id="price" type="number" placeholder="95.50" className="mt-1.5" />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="min">Мин. сумма ($)</Label>
                        <Input id="min" type="number" placeholder="100" className="mt-1.5" />
                      </div>
                      <div>
                        <Label htmlFor="max">Макс. сумма ($)</Label>
                        <Input id="max" type="number" placeholder="5000" className="mt-1.5" />
                      </div>
                    </div>
                    
                    <div>
                      <Label htmlFor="currency">Валюта</Label>
                      <Input id="currency" placeholder="USDT" className="mt-1.5" />
                    </div>
                    
                    <Button className="w-full bg-primary hover:bg-primary/90" size="lg" onClick={() => toast.success('Объявление создано')}>
                      <Icon name="Plus" size={18} className="mr-2" />
                      Опубликовать объявление
                    </Button>
                  </div>
                </div>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="deals" className="space-y-4 animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-semibold">Мои сделки</h2>
              <Badge variant="outline" className="text-sm">
                {mockDeals.filter(d => d.status !== 'completed' && d.status !== 'cancelled').length} активных
              </Badge>
            </div>
            {mockDeals.map((deal) => (
              <Card key={deal.id} className="p-6 bg-card border-border">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <Icon name={deal.type === 'buy' ? 'ArrowDown' : 'ArrowUp'} 
                            size={20} 
                            className={deal.type === 'buy' ? 'text-green-500' : 'text-blue-500'} />
                      <span className="font-semibold text-lg">
                        {deal.type === 'buy' ? 'Покупка' : 'Продажа'} {deal.currency}
                      </span>
                      <Badge className={`${getStatusColor(deal.status)} hover:${getStatusColor(deal.status)}`}>
                        {getStatusText(deal.status)}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="text-muted-foreground">Сумма</div>
                        <div className="font-semibold">${deal.amount}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Цена</div>
                        <div className="font-semibold">${deal.price}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Контрагент</div>
                        <div className="font-semibold">{deal.counterparty}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Дата</div>
                        <div className="font-semibold">{deal.date}</div>
                      </div>
                    </div>
                  </div>
                  {deal.status === 'escrow' && (
                    <div className="flex gap-2 ml-4">
                      <Button size="sm" className="bg-primary hover:bg-primary/90" onClick={() => toast.success('Сделка завершена')}>
                        Завершить
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => toast.error('Спор открыт')}>
                        Спор
                      </Button>
                    </div>
                  )}
                </div>
                {deal.status === 'escrow' && (
                  <div className="mt-4 p-4 bg-primary/10 rounded-lg border border-primary/20">
                    <div className="flex items-center gap-2 text-sm">
                      <Icon name="Shield" size={16} className="text-primary" />
                      <span className="text-primary font-medium">Средства в эскроу</span>
                      <span className="text-muted-foreground">— Ваши деньги защищены до завершения сделки</span>
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
