import React, { useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { CheckCircle, XCircle, ArrowRight } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export const MarketplaceSuccess = () => {
  const [searchParams] = useSearchParams();
  const purchaseId = searchParams.get('purchase_id');
  const orderId = searchParams.get('token'); // PayPal returns order ID as 'token'

  // If we have an order ID from PayPal's full API, capture the payment
  const { data: captureResult } = useQuery({
    queryKey: ['capture-order', orderId],
    queryFn: () => axios.post(`${API}/paypal/capture-order`, { order_id: orderId }).then(r => r.data),
    enabled: !!orderId && orderId !== purchaseId,
    retry: false
  });

  return (
    <div className="min-h-screen pt-20 px-4 flex items-center justify-center">
      <StarsBackground />
      <Card className="card-glass p-8 max-w-md text-center" data-testid="payment-success">
        <CheckCircle className="mx-auto text-green-400 mb-4" size={64} />
        <h1 className="text-2xl font-bold text-gradient-gold mb-4">Payment Successful! 🎉</h1>
        <p className="text-white/70 mb-6">
          Thank you for your purchase! The protocol has been added to your collection.
        </p>
        {purchaseId && (
          <p className="text-white/50 text-sm mb-4">Purchase ID: {purchaseId}</p>
        )}
        <div className="flex flex-col gap-3">
          <Link to="/search">
            <Button className="btn-gold w-full">
              <ArrowRight className="mr-2" size={16} /> Go to Ultimate Search
            </Button>
          </Link>
          <Link to="/marketplace">
            <Button variant="outline" className="w-full">Browse More Protocols</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
};

export const MarketplaceCancel = () => {
  return (
    <div className="min-h-screen pt-20 px-4 flex items-center justify-center">
      <StarsBackground />
      <Card className="card-glass p-8 max-w-md text-center" data-testid="payment-cancelled">
        <XCircle className="mx-auto text-red-400 mb-4" size={64} />
        <h1 className="text-2xl font-bold text-white mb-4">Payment Cancelled</h1>
        <p className="text-white/70 mb-6">
          Your payment was cancelled. No charges have been made.
        </p>
        <div className="flex flex-col gap-3">
          <Link to="/marketplace">
            <Button className="btn-gold w-full">Return to Marketplace</Button>
          </Link>
          <Link to="/">
            <Button variant="outline" className="w-full">Go Home</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
};

export default MarketplaceSuccess;
