import React, { useState } from 'react';
import { Autocomplete, TextField } from '@mui/material';
import { PlaceDTO } from '../../api/types';
import { useGeocodeSearch } from '../../hooks/useGeocodeSearch';

export interface PlaceAutocompleteProps {
  id: string;
  label: string;
  placeholder?: string;
  value: PlaceDTO | null;
  onChange: (value: PlaceDTO | null) => void;
  error?: string;
  helperText?: string;
  disabled?: boolean;
  'data-testid'?: string;
}

export const PlaceAutocomplete: React.FC<PlaceAutocompleteProps> = ({
  id,
  label,
  placeholder,
  value,
  onChange,
  error,
  helperText,
  disabled = false,
  'data-testid': testId,
}) => {
  const [prevValue, setPrevValue] = useState<PlaceDTO | null>(value);
  const [inputValue, setInputValue] = useState(value ? value.label : '');
  const [open, setOpen] = useState(false);

  // Sync inputValue when value changes externally (e.g. swap or example trip)
  if (value !== prevValue) {
    setPrevValue(value);
    setInputValue(value ? value.label : '');
  }

  const { data: places, isLoading } = useGeocodeSearch(inputValue);

  return (
    <Autocomplete<PlaceDTO>
      id={id}
      disabled={disabled}
      open={open && inputValue.trim().length >= 3}
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
      value={value}
      onChange={(_, newValue) => {
        onChange(newValue);
      }}
      inputValue={inputValue}
      onInputChange={(_, newInputValue, reason) => {
        if (reason === 'input' || reason === 'clear') {
          setInputValue(newInputValue);
          if (newInputValue === '') {
            onChange(null);
          }
        }
      }}
      onBlur={() => {
        // Enforce picking a result: revert input text to chosen place on blur
        setInputValue(value ? value.label : '');
      }}
      options={places || []}
      getOptionLabel={(option) => option.label}
      isOptionEqualToValue={(option, val) =>
        Boolean(
          val &&
            option.lat === val.lat &&
            option.lon === val.lon &&
            option.label === val.label,
        )
      }
      filterOptions={(options) => options} // Filtered upstream by TomTom geocoding API
      loading={isLoading}
      noOptionsText={
        inputValue.trim().length < 3
          ? 'Type at least 3 characters'
          : 'No matches'
      }
      loadingText="Searching places..."
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          placeholder={placeholder}
          error={Boolean(error)}
          helperText={error || helperText}
          size="small"
          fullWidth
          slotProps={{
            ...params.slotProps,
            htmlInput: {
              ...params.slotProps.htmlInput,
              'data-testid': testId || `${id}-input`,
            },
          }}
        />
      )}
    />
  );
};
