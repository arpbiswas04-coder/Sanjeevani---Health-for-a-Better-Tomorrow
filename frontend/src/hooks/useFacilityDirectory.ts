import { useBackendData } from './useBackendData';
import { FacilityView, CountryView, StateView, DistrictView, BlockView } from '@/services/backendTypes';
import { QueryParams } from '@/services/dataApi';

export function useFacilityDirectory(params: QueryParams = {}) {
  const facilities = useBackendData<FacilityView[]>('/facilities', params, 'inventory.read', true, true);
  const countries = useBackendData<CountryView[]>('/geography/countries', {}, 'inventory.read', true, true);
  const states = useBackendData<StateView[]>('/geography/states', {}, 'inventory.read', true, true);
  const districts = useBackendData<DistrictView[]>('/geography/districts', {}, 'inventory.read', true, true);
  const blocks = useBackendData<BlockView[]>('/geography/blocks', {}, 'inventory.read', true, true);
  const location = (facility: FacilityView) => {
    const block = blocks.data?.find(b => b.id === facility.block_id);
    const district = districts.data?.find(d => d.id === block?.district_id);
    const state = states.data?.find(s => s.id === district?.state_id);
    const country = countries.data?.find(c => c.id === state?.country_id);
    return { block, district, state, country };
  };
  const geographyPending = [countries, states, districts, blocks].some(query => query.isPending);
  const geographyUnavailable = [countries, states, districts, blocks].some(query => !!query.error);
  return { facilities, countries, states, districts, blocks, location, geographyPending, geographyUnavailable };
}
