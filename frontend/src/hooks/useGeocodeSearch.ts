import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { searchPlaces } from '../api/geocodeApi';
import { GeocodePlaceDTO } from '../api/types';
import { useDebouncedValue } from './useDebouncedValue';

/**
 * Geocode place search query hook with 300ms debouncing, min 3 characters requirement,
 * and previous data preservation.
 */
export function useGeocodeSearch(query: string) {
  const debouncedQuery = useDebouncedValue(query.trim(), 300);
  const enabled = debouncedQuery.length >= 3;

  return useQuery<GeocodePlaceDTO[]>({
    queryKey: ['geocode', debouncedQuery],
    queryFn: ({ signal }) => searchPlaces(debouncedQuery, signal),
    enabled,
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
  });
}
