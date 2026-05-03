import { TransactionTable } from '../components/table/TransactionTable'
import { MOCK_TRANSACTIONS } from '../lib/mockData'

export function Transactions() {
  return (
    <div className="h-full flex flex-col overflow-hidden">
      <TransactionTable
        transactions={MOCK_TRANSACTIONS}
        isLoading={false}
      />
    </div>
  )
}
